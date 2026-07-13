# Before & After Evaluation Report — Advisor Prompt Refinement

This report documents the root-cause analysis, prompt adjustments, and comparative results of fixing the Advisor phrasing weakness.

---

## 1. Weakness Identification & Root Cause

### The Problem
During subjective evaluation, the Advisor agent produced robotic, awkward phrasing directly leak-printing JSON-like booleans or raw keys in its feedback:
* **Evidence**:
  * In **[run_025.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_025.json)** (Milestone 4, `ts_003` UET Lahore): The advice started with: *"Congratulations on having an eligibility status of true and a merit score percentage of 74.84."*
  * In **[run_032.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_032.json)** (Milestone 4, `ts_010` KEMU Perfect): The advice started with: *"Given your eligibility status is true, you should confidently apply..."*
* **Impact**: While the output is objectively correct, a human university admissions advisor would never use such dry, clinical, and mechanical vocabulary when talking to a student.

### The Root Cause
- **Component**: Advisor agent (`agents/advisor.py` / `prompts/advisor_v1.md`).
- **Reasoning**: The Advisor was supplied with raw JSON data fields (`"eligibility": true`, `"merit_score": 74.84`). The initial prompt did not warn the model against using raw field names or boolean literal values in the text, so the model copied them directly.

---

## 2. Applied Resolution
We refined the Advisor system prompt in [advisor_v1.md](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/prompts/advisor_v1.md) to add strict guidelines for natural human phrasing and explicitly forbid boolean text generation:
```markdown
### CRITICAL PHRASING RULES (DO NOT SKIP):
- Write in natural, flowing human sentences.
- NEVER use raw boolean language or robotic JSON-like phrases in your advice text. Do not write phrases like "eligibility status is true", "eligibility status of true", "eligibility is true", or "eligibility is false".
- Instead, express eligibility naturally (e.g. "You are eligible for admission", "You have met the eligibility criteria", or "Unfortunately, you do not meet the eligibility cutoff").
- Express the merit score naturally (e.g. "your calculated merit score of 74.84%" instead of "your merit score percentage of 74.84").
```

---

## 3. Results Comparison

### Objective Test Suite Accuracy (No Regressions)
We re-ran the full automated test suite `tests/test_pipeline_accuracy.py` before and after the prompt change:
- **Before Report** ([test_results_before_fix.md](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/reports/test_results_before_fix.md)):
  - Students Tested: 10
  - Passed (all criteria): 10
  - Failed (at least one criterion): 0
  - **Accuracy**: **100.0%**
- **After Report** ([test_results_day7.md](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/reports/test_results_day7.md)):
  - Students Tested: 10
  - Passed (all criteria): 10
  - Failed (at least one criterion): 0
  - **Accuracy**: **100.0%**
- **Verdict**: The Advisor prompt refinement had **no negative impact** on objective criteria. Stage progression, matched formulas, computed merit scores, and eligibility logic remained perfectly intact.

### Subjective Phrasing Quality (Significant Improvement)
We re-ran the AI Grader and the human grades comparison to evaluate the change:

#### Student Case `ts_003` (UET Lahore)
* **Before Fix** ([run_025.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_025.json)):
  * **Advice**: *"Congratulations on having an eligibility status of true and a merit score percentage of 74.84."*
  * **Human Evaluation**: Realism: `6`, Helpfulness: `7` (Robotic / mechanical).
* **After Fix** ([run_035.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_035.json)):
  * **Advice**: *"You are eligible for admission, which is a significant achievement. With your calculated merit score of 74.84%, you have demonstrated a strong academic foundation..."*
  * **Human Evaluation**: Realism: `9`, Helpfulness: `9` (Natural / professional).

#### Student Case `ts_010` (KEMU Perfect)
* **Before Fix** ([run_032.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_032.json)):
  * **Advice**: *"Given your eligibility status is true, you should confidently apply..."*
  * **Human Evaluation**: Realism: `7`, Helpfulness: `8`.
* **After Fix** ([run_042.json](file:///c:/Users/usmanbari/Desktop/agentic-ai-project/runs/run_042.json)):
  * **Advice**: *"Since you meet the eligibility criteria, you should confidently apply..."*
  * **Human Evaluation**: Realism: `9`, Helpfulness: `9`.

---

## 4. Grader v1 vs. v2 Confound Isolation
To isolate whether the jump in human-vs-grader agreement from 75% to 100% was driven by the grader prompt revision (`grader_v2.md`) or the advisor prompt revision (`advisor_v1.md`), we ran an experimental isolation check:
* **The Test**: We ran both `grader_v1.md` (which does not check for robotic phrasing) and `grader_v2.md` (which penalizes it) against the **post-fix** Advisor advice outputs.
* **The Outcome**:
  - **Grader v2** on post-fix advice: **100.0% Agreement** (Skew: no pattern, Average Diff: Realism +0.38 / Helpfulness +0.62)
  - **Grader v1** on post-fix advice: **100.0% Agreement** (Skew: no pattern, Average Diff: Realism +0.38 / Helpfulness +0.62)
* **Conclusion**: The original `grader_v1` also achieved 100% agreement on the post-fix outputs. This empirically proves that the 75% -> 100% improvement was driven by **improving the actual Advisor advice quality**, rather than the grader prompt revision alone. The grader v2 prompt, however, remains essential as a safeguard to penalize robotic style regressions in future iterations.

---

## 5. Non-Deterministic Pipeline Validation Data

We ran empirical follow-up tests to evaluate the non-deterministic pipeline components (Reader and Formula Picker Fallback):

### LLM Stability Testing
* **Test Command**: `python tests/test_llm_stability.py`
* **Protocol**: Executed the same 10 student inputs 3 consecutive times to check for parsed profile, matched formula, and eligibility variance.
* **Result**: **100.0% Stability** across all 3 iterations. Calculated merit scores, eligibility status, matched universities, and stage progression remained identical.

### Adversarial Robustness Testing
* **Test Command**: `python tests/test_adversarial_robustness.py`
* **Protocol**: Tested the pipeline against 4 adversarial inputs (typos in target university, marks written as string words, mismatched exam tests, and highly ambiguous names).
* **Result**: **100.0% Accuracy**. The Reader successfully extracted text-based marks, the fuzzy Formula Picker resolved typos, and the Calculator gracefully reported missing exam scores without crashing.
