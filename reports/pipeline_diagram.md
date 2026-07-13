# Pipeline Architecture Diagram

This diagram visualizes the data flow across our Admission Advisor pipeline (Milestone 2).

```
Student Input
     │
     ▼
Reader (LLM) ──────────► student_profile (marks w/ obtained+total, university_raw)
     │
     ▼
Formula Picker (code, LLM fallback) ──► formula (weights + display string)
     │
     ▼
Calculator (pure code, normalizes marks to % first) ──► merit_score, eligibility
     │
     ▼
Advisor (LLM) ────────────────────────► advice
     │
     ▼
Final State (stage="complete", saved to runs/ with intermediate_outputs)
```
