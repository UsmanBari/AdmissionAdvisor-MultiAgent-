# Pipeline Information Table (Milestone 2 Forward Planning)

This table serves as the design brief and reference specification for the 5-step multi-agent pipeline in Milestone 2.

| Step | Input | Context (allowed to see) | Output | Failure modes |
|---|---|---|---|---|
| Reader | messy text | instructions only | structured JSON (marks, university) | missing marks, misparsed field, misspelled/unrecognized university |
| Formula Picker | university name | instructions + official formula reference table | matching formula, or "not found" | university not in list, fuzzy name mismatch |
| Calculator | clean marks + formula | no LLM — just data, plain code | merit score | wrong weight applied, missing subject score, division error |
| Advisor | profile + score + eligibility | instructions + those three fields only | advice text | generic/templated advice, ignores eligibility, overconfident tone |
| Checker | advisor's output only | instructions + advisor's output | pass/fail + reason | too lenient, too harsh, misses a factual error |
