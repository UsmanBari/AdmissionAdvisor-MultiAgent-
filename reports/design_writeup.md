# System Design Document — Milestone 3 & Extensions

This document outlines the architectural design, component responsibilities, quality control loop rationale, and error handling behaviors of the **Admission Advisor System**.

---

## 1. Component Responsibilities & Boundaries

To achieve modularity and prevent the system failures seen in the single-agent baseline (where the LLM had to perform extraction, formula lookup, math, and advice in a single call), the pipeline is partitioned into distinct components, each with strict single-responsibility boundaries.

### Reader Agent (`agents/reader.py`)
* **Responsible for**: Parsing the raw student text to extract numeric marks, associated total denominators (if stated), and the target university name as written. Outputting data in a structured, static JSON schema.
* **NOT responsible for**: Calculating merit scores, verifying if marks are complete, determining admission eligibility, selecting formulas, or writing recommendations.

### Formula Picker (`agents/formula_picker.py`)
* **Responsible for**: Matching the raw university name to an entry in `data/formulas.json`. It executes a code-first exact match and alias match (e.g. mapping "KEMU" or "King Edward" to "King Edward Medical University"). If code matching fails, it fuzzy-matches using the LLM fallback (which only receives a list of official names as context).
* **NOT responsible for**: Storing formulas in memory (they must live in `formulas.json`), calculating scores, or checking the validity of student marks.

### Calculator (`tools/calculator.py`)
* **Responsible for**: Performing pure mathematical computations. It normalizes all raw marks to percentages first, loads standard totals if the student did not state them, multiplies by formula weights, and calculates a final percentage-based merit score. It also evaluates eligibility against a temporary 50% cutoff.
* **NOT responsible for**: Running LLM calls, parsing raw text, fuzzy-matching university names, or writing advice. It is a **pure python tool** with no external LLM dependencies.

### Advisor Agent (`agents/advisor.py`)
* **Responsible for**: Writing encouragement and honest recommendations to the student. It receives the structured profile, the university formula, the computed merit score, and the eligibility. It also handles revisions by accepting previous drafts and correction feedback to produce an updated version.
* **NOT responsible for**: Performing arithmetic calculations, determining eligibility status, or verifying if the student's marks match the university requirements.

### Checker Agent (`agents/checker.py`)
* **Responsible for**: Quality assurance. It reviews the Advisor's advice and cross-checks it against the `merit_score` and `eligibility` to verify that the advice is realistic, consistent, and honest. It produces an approval verdict (`approved: true/false`) and feedback.
* **NOT responsible for**: Editing advice text, reading raw student input, looking up formulas, or doing calculations. It cannot modify advice; it can only approve or reject it.

---

## 2. Rationale for the Checker's Restricted Context

The Checker agent is explicitly restricted to see **only** the `merit_score`, the `eligibility` status, and the Advisor's `advice` string. It is denied access to the raw student description, the university formula, and intermediate extraction outputs.

### Rationale:
1. **Prevention of Goal Drift**: If the Checker had access to raw marks or formulas, it would be tempted to re-calculate the merit score or verify if the picker selected the right formula. This would turn the Checker into a secondary Advisor/Calculator, increasing API latency, tokens cost, and likelihood of math hallucinations.
2. **True QA Isolation**: QA is concerned with the consistency of the final delivery. The Checker's single query is: *"Given this score and eligibility, is this advice honest and accurate?"* By matching advice text (e.g., "you got accepted!") with the eligibility boolean (e.g., `False`), it acts as a precise logical validator.
3. **Decoupled Architecture**: Restricting context enforces clear API boundaries. If the internal logic of the Reader or Picker changes in future milestones, the Checker's logic remains completely unaffected because its input contract is minimal.

---

## 3. Rationale for the Single-Rewrite Cap (`MAX_REWRITES = 1`)

The quality checking loop is capped at exactly one rewrite. If the Checker rejects the advice a second time, the pipeline terminates, and the advice is delivered with the checker's verdict recorded as `approved: false`.

### Rationale:
1. **Avoiding Infinite Loops**: If a model gets stuck in a hallucination pattern, a loose loop could cycle indefinitely, exhausting API rate limits and generating unnecessary costs.
2. **Determinism and Predictability**: In production systems, request-response durations must be bounded. A hard-cap of 1 rewrite ensures that a request takes at most 2 advisor runs and 2 checker runs, placing a predictable ceiling on latency.
3. **Telemetry and Transparency**: If an advisor consistently generates bad advice that the checker rejects, the system should log the unresolved failure (`approved: false`) to notify developers, rather than silently looping or patching.

---

## 4. Evidence of Error and Failure Handling

The pipeline behaves predictably and gracefully under failures without throwing stack traces or crashing the program.

### Example A: Unresolved Fuzzy Matching Failure (Formula Picker)
In **[run_018.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_018.json)**, the student applied to `"Greenwood Institute of Science and Technology"`.
- **Result**: The Picker could not find the university in `formulas.json` nor could the LLM fuzzy match it.
- **Graceful Termination**: The pipeline did not crash. It caught the failure, set `stage = "failed_at_formula_picker"`, appended `"University 'Greenwood Institute of Science and Technology' could not be matched..."` to `errors`, saved the run file, and returned the state immediately.

### Example B: Missing Required Marks (Calculator)
In **[run_021.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_021.json)**, the student did not provide an MDCAT score when applying to King Edward Medical University.
- **Result**: The Calculator identified that `mdcat` is a required field in the KEMU formula but was missing (`null`).
- **Graceful Termination**: The Calculator returned an error string. The pipeline captured it, appended `'missing required mark: mdcat'` to `errors`, set `stage = "failed_at_calculator"`, saved the run file, and stopped execution.

### Example C: Rejection and Correction (Checker and Rewrite Loop)
In **[run_022.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_022.json)** (the deliberate rejection test case):
- **Attempt 1**: The Advisor's output was mocked to say: *"Great news! You are fully eligible... you will easily get in!"*
- **Rejection**: The Checker saw a merit of `26.14`, eligibility `False`, and advice claiming the student was eligible. It immediately failed the advice: `approved: false` with the reason: *"The advice is inconsistent with the eligibility status, which is marked as false... yet the advice states the student is fully eligible."*
- **Correction**: The pipeline incremented `rewrite_count` to 1. It fed a structured correction payload back to the Advisor. The Advisor corrected itself, producing honest advice: *"with a merit score of 26.14%, you currently don't meet the eligibility criteria. Don't be discouraged..."*
- **Second Verdict**: The Checker reviewed the rewritten advice and approved it: `approved: true`. The stage was successfully marked as `"complete"`, and the run history preserved both attempts.

---

## 5. Memory Cache Design Rationale (Extension)

### Placement of Caching Logic
The caching system is deliberately placed **after the Reader and Formula Picker stages**, but **before the Calculator, Advisor, and Checker stages**.
* **Why not before the Reader?** 
  Students write their inquiries in free-text with highly varied phrasing (e.g. "I got 970/1100 in FSC" vs "FSC marks: 970"). Caching on the raw input string would result in a very low cache hit rate. By running the Reader and Picker first, we extract a structured profile and resolve the official matched university name.
* **Stable Cache Key**:
  We sort the keys of the parsed `marks` dictionary and combine them with the matched university name into a sorted, deterministic JSON string. We then generate a SHA-256 hash of this string to act as the cache key.
* **What gets bypassed?**
  On a cache hit, we bypass the Calculator (deterministic Python script) and the Advisor and Checker (probabilistic LLM agents). Bypassing the Advisor and Checker LLM calls is where the real value lies, cutting execution latency from ~5 seconds down to under 50ms and eliminating API token costs.
