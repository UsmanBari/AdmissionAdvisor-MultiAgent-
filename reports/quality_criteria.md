# Quality Criteria Brief

This document establishes the validation parameters and testing requirements for the Admission Advisor System outputs.

## Evaluation Criteria

### 1. Objective Metrics (Actively Evaluated Now)
- **Stage Progression**: The pipeline must terminate at the correct expected execution stage (e.g. `complete`, `failed_at_formula_picker`, `failed_at_calculator`).
- **University Matched**: The matched university from `formulas.json` (exact key name) must be resolved correctly.
- **Formula Display**: The formula text expression must match the expected configuration display exactly.
- **Merit Score Precision**: The calculated merit score percentage must be correct within a **±0.01%** floating-point tolerance compared to the hand-calculated expectation.
- **Eligibility Accuracy**: The boolean eligibility status must match the expected evaluation based on the temporary $50\%$ cutoff.

### 2. Subjective Metrics (Deferred to Milestone 5)
- **Sensible Recommendations**: Determining whether recommendations align logically with the student's marks and target field. (Deferred to Milestone 5 AI Grader).
- **Encouraging and Honest Tone**: Analyzing whether advice is encouraging yet realistic and direct. (Deferred to Milestone 5 AI Grader).

---

## Configuration Reference Freeze Policy

> [!WARNING]
> The `data/formulas.json` used to build this answer key is frozen for the duration of testing. If it changes, every hand-calculated expected value must be re-verified before re-running tests — a formula change is not a test failure, it's a stale answer key.

- **Answer Key Build Date**: 2026-07-11
- **Pipeline Version Reference**: `v3` (Milestone 3 Scaffolding)

---

### Determinism Breakdown

The 100% accuracy figure in Milestone 4 reflects a pipeline made of both deterministic and non-deterministic components. This table exists to make clear what that 100% does and doesn't prove.

| Step | Nature | Why | What 100% here proves |
|---|---|---|---|
| Reader | Non-deterministic (LLM) | Free-text parsing, no fixed logic path | Almost nothing on its own — one clean run of a probabilistic component isn't evidence of its true success rate |
| Formula Picker (primary path) | Deterministic (code) | Plain string/alias lookup against `formulas.json`, no LLM involved | Expected to always be 100% if the lookup code has no bugs — correctness here is a code-correctness check, not a robustness check |
| Formula Picker (fallback path) | Non-deterministic (LLM) | Only triggered for unmatched names, fuzzy-matches against the university list | Not exercised by most of the 10 test students — the fallback's real reliability is largely untested by this suite |
| Calculator | Deterministic (code) | Pure Python, zero LLM calls | 100% here is guaranteed by correct code and hand-verified math — it says nothing about the system's handling of messy real-world input |
| Advisor | Non-deterministic (LLM) | Free-text generation | Excluded entirely from Milestone 4's objective checks — quality here is only assessed in Milestone 5 |
| Checker | Non-deterministic (LLM) | Judgment call on approval | Same — not covered by the 100% figure |

**What the 100% actually demonstrates:** the deterministic core (Calculator's normalization/weighting math, Formula Picker's primary lookup) is bug-free against the hand-calculated answer key. It does not demonstrate that Reader reliably parses varied real-world phrasing, or that the Formula Picker's LLM fallback reliably resolves misspelled/unusual university names, since each test student was run through the pipeline only once.

**Known gap, not yet covered by testing:** repeated runs of the same non-deterministic steps to measure actual variance, and adversarial inputs (typos, marks written as words, ambiguous or conflicting info) that specifically stress the LLM-dependent steps rather than the deterministic ones.
