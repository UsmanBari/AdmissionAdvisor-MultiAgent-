# Component Stress-Test Findings

This document summarizes the results of the isolated stress-testing pass performed on the Admission Advisor system components: Reader, Calculator, Formula Picker, and Checker. 

The primary objective was to push each component to its breaking point under adversarial inputs and classify outcomes as **SAFE**, **CAUGHT GRACEFULLY**, **SILENT WRONG ANSWER**, or **CRASHED**.

---

## 🚨 Critical Silent Wrong Answers

The following cases represent **Silent Wrong Answers**. These are the most dangerous class of failure modes because they calculate or parse incorrect data without triggering code-level errors or pipeline warnings, meaning they go completely unnoticed in a standard run.

### 1. Reader: Random Numbers Mapped to Subjects (`970 1010 185`)
* **Input**: `"970 1010 185"`
* **Behavior**: The Reader extracted these numbers and matched them to `matric` (obtained 970, total 1010) and `fsc` (obtained 185, total null).
* **Why it's dangerous**: The LLM hallucinated the subject associations entirely without context, fabricating a plausible-looking student profile from random integers.

### 2. Reader: Cherried/Merged Marks Across Universities (`KEMU... FSC 1000... NUST... FSC 980...`)
* **Input**: `"I want to apply to KEMU. My FSC is 1000 and Matric is 950. Also I want to apply to NUST where my FSC is 980 and Matric is 940, and to UET with FSC 900."`
* **Behavior**: The Reader parsed target universities as `"KEMU, NUST, UET"`, but merged the marks, mapping `matric` to 950 and `fsc` to 980 (taking NUST's FSC and KEMU's Matric).
* **Why it's dangerous**: When a student mentions multiple schools with distinct scores, the Reader aggregates them into a single student profile rather than rejecting the query as ambiguous, leading to a mismatched final merit score.

### 3. Reader: Hallucinated Totals on Self-Contradiction (`950 in FSC but FSC is actually 920`)
* **Input**: `"I got 950 in FSC but my FSC score is actually 920. KEMU is the university."`
* **Behavior**: The Reader parsed FSC as `obtained: 950` and `total: 920`.
* **Why it's dangerous**: The Reader interpreted the contradiction as a fraction (`950/920`) instead of highlighting the ambiguity, which propagates a physically impossible >100% component score downstream.

### 4. Calculator: Overflow Marks and Negative Marks
* **Inputs**: Obtained marks higher than total (`obtained=1200, total=1100`) or negative marks (`obtained=-50`).
* **Behavior**: The Calculator divided the values and multiplied by weights, yielding component percentages of `109.09%` and `-4.54%` respectively. It outputted final merit scores like `90.91%` and `34.09%` with no errors.
* **Why it's dangerous**: Pure math calculation trusts input boundaries blindly, allowing students with negative scores or scores exceeding the denominator to be processed.

### 5. Calculator: Blind Formula Weight Trust
* **Input**: A formula with weights that sum to `0.8` instead of `1.0` (`{"matric": 0.5, "fsc": 0.3}`).
* **Behavior**: The Calculator computed a merit of `80.0%` for a student with perfect 100% scores in both subjects, returning it as a valid eligibility pass.
* **Why it's dangerous**: If configuration files or Picker fallbacks supply a broken formula structure, the math executes without auditing the weight sum.

### 6. Formula Picker: Ambiguous Substring Matching (`Lahore`)
* **Input**: `"Lahore"`
* **Behavior**: The Picker's fuzzy LLM fallback matched this to `"UET Lahore"`, ignoring `"FAST NUCES"`.
* **Why it's dangerous**: The picker matched the first plausible candidate without identifying that the term could refer to multiple registered entities.

### 7. Checker: Rejection of Factual Advice Due to Tone (`salesy_but_correct`)
* **Input**: Factual advice for 90.7% merit, written as `"OMG! You are a superstar! You are 100% eligible for King Edward Medical University! Go celebrate! ..."`
* **Behavior**: The Checker rejected the advice as `"overly enthusiastic and unrealistic"`, claiming a score of 90.7% is not "phenomenal" or a "guarantee".
* **Why it's dangerous**: The Checker mixed subjective tone judgments with objective fact checks, resulting in incorrect rejections of mathematically sound drafts.

---

## 📊 Summary Test Results Grid

| Component Tested | Adversarial Input | Outcome | Verdict |
|---|---|---|---|
| **Reader** | `"alkjfdskfjhasdkjfh"` (nonsense) | Null marks, `university_raw` set to raw nonsense | **SAFE** |
| **Reader** | `"970 1010 185"` (numbers only) | Matric mapped to `970/1010`, FSC to `185` | 🚨 **SILENT WRONG ANSWER** |
| **Reader** | `"I want to apply to KEMU... NUST..."` (multi-uni) | Mixed-and-matched scores from different sentences | 🚨 **SILENT WRONG ANSWER** |
| **Reader** | `"Mera FSC me 980 marks hain..."` (Urdu code-switch) | Successfully extracted FSC 980, Matric 1010, KEMU | **SAFE** |
| **Reader** | `"5000 in matric, 4500 in FSC"` (impossible) | Extracted obtained marks: `5000` and `4500` | 🚨 **SILENT WRONG ANSWER** |
| **Reader** | `"   "` (empty input) | Markdown block returned by LLM, causing JSON load crash | 💥 **CRASHED (CAUGHT)** |
| **Reader** | `"950 in FSC but FSC is 920"` (contradiction) | Extracted FSC obtained: `950`, total: `920` | 🚨 **SILENT WRONG ANSWER** |
| **Calculator** | `obtained = 0` (boundary mark) | Merit computed to `36.36%`, eligibility `False` | **SAFE** |
| **Calculator** | `obtained = 1200, total = 1100` (overflow mark) | Merit computed to `90.91%` (component is `109.09%`) | 🚨 **SILENT WRONG ANSWER** |
| **Calculator** | `obtained = -50` (negative mark) | Merit computed to `34.09%` (component is `-4.54%`) | 🚨 **SILENT WRONG ANSWER** |
| **Calculator** | `total = 0` (division by zero) | Returns error dictionary indicating missing total | **CAUGHT GRACEFULLY** |
| **Calculator** | Merit computing to exactly `50.0%` (cutoff) | Computed `50.0%`, eligibility `True` | **SAFE** |
| **Calculator** | Weights sum to `0.8` (broken weights) | Computed `80.0%` merit on perfect scores | 🚨 **SILENT WRONG ANSWER** |
| **Formula Picker** | `"Lahore"` (ambiguous substring) | Fuzzy matched to `"UET Lahore"` | 🚨 **SILENT WRONG ANSWER** |
| **Formula Picker** | `""` (empty string) | Returns `found: false` with not-found error | **CAUGHT GRACEFULLY** |
| **Formula Picker** | `"   kEmU   "` (spacing and casing) | Direct matched to `"King Edward Medical University"` | **SAFE** |
| **Formula Picker** | `"KEMU or NUST"` (multiple universities) | Matched to `"NUST"` (fuzzy fallback selected one) | 🚨 **SILENT WRONG ANSWER** |
| **Formula Picker** | `"Hogwarts..."` (fictional name) | Fuzzy fallback returned `found: false` | **CAUGHT GRACEFULLY** |
| **Checker** | salesy tone, correct facts (`90.7%`, `True`) | Rejected because of enthusiastic tone | 🚨 **SILENT WRONG ANSWER** |
| **Checker** | program mismatch (recommended KEMU at `55.0%`) | Rejected for offering unrealistic guarantees at 55.0% | **SAFE** |
| **Checker** | `"You're eligible. Good luck."` (low effort) | Rejected for being brief and unhelpful | **SAFE** |
| **Checker** | false cs guarantee at `50.1%` (boundary) | Rejected for guaranteeing competitive CS selection | **SAFE** |

---

## 🛠️ Prioritized Backlog: "If we had more time..."

Based on risk severity (Silent Wrong Answers > Code Crashes > Graceful-but-unhelpful), here is the ranked list of fixes we would prioritize first:

### 1. [Rank 1] Calculator: Bounds and Schema Checks (Silent Wrong Answer)
* **Problem**: The Calculator blindly performs math on whatever floats it receives, yielding negative percentages, values over 100%, and processing formulas whose weights do not sum to 1.0.
* **Fix**: 
  1. Raise a validation error if any parsed mark `obtained` value is negative or exceeds `total`.
  2. Verify that `sum(formula.values()) == 1.0` before running calculation.

### 2. [Rank 2] Reader: Ambiguity and Contradiction Detection (Silent Wrong Answer)
* **Problem**: The Reader merges data when a user inputs contradictory statements or multiple target schools, creating hybrid student records.
* **Fix**: Instruct the Reader in the system prompt to check for multiple schools or contradictory scores for the same subject and output an `"ambiguous": true` flag in the JSON if detected, halting the pipeline at the Reader stage.

### 3. [Rank 3] Formula Picker: Ambiguity Resolution (Silent Wrong Answer)
* **Problem**: When multiple universities match a search query, the Picker selects one arbitrarily via the LLM fuzzy match.
* **Fix**: If the LLM fuzzy match returns multiple potential universities, the Picker should mark `found: false` and list the alternatives, prompting the user to clarify.

### 4. [Rank 4] Checker: Focus Isolation (Silent Wrong Answer)
* **Problem**: The Checker rejects correct advice when written in an enthusiastic, salesy tone.
* **Fix**: Refine the Checker system prompt to distinguish between *factual inaccuracies/unrealistic guarantees* (which must be rejected) and *syntactic style/enthusiastic tone* (which should be tolerated).

### 5. [Rank 5] Reader: Whitespace Code-Block Parsing (Code Crash)
* **Problem**: When given whitespace-only inputs, the Reader LLM wraps JSON inside markdown block ticks (```json ... ```), crashing `json.loads`.
* **Fix**: Implement a utility that strips codeblock ticks from the LLM response text before passing it to the JSON parser.
