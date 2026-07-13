# Grader Trust Analysis — grader_v2.md

## Metadata
- **Analysis Run Timestamp**: `2026-07-11T12:16:47+05:00`
- **Grader Prompt Version**: `grader_v2.md`
- **Human Grades Source**: `reports/human_grades.json`
- **Grader Scores Source**: `reports/grader_scores.json`

## Evaluation Summary
- **Overall Agreement Rate**: 100.0% (defined as absolute difference < 2 points)
- **Disagreement Skew Direction**: no consistent pattern
- **Average Realism Score Difference**: +0.38 (Grader - Human)
- **Average Helpfulness Score Difference**: +0.62 (Grader - Human)

## Per-Case Comparison Grid

| Student ID | Realism (H / G) | Realism Diff | Status | Helpfulness (H / G) | Helpfulness Diff | Status |
|---|---|---|---|---|---|---|
| ts_001 | 9 / 10 | +1 | `OK` | 9 / 10 | +1 | `OK` |
| ts_002 | 9 / 9 | +0 | `OK` | 9 / 9 | +0 | `OK` |
| ts_003 | 9 / 9 | +0 | `OK` | 9 / 9 | +0 | `OK` |
| ts_004 | 9 / 9 | +0 | `OK` | 8 / 9 | +1 | `OK` |
| ts_005 | 9 / 9 | +0 | `OK` | 8 / 9 | +1 | `OK` |
| ts_006 | 8 / 9 | +1 | `OK` | 8 / 9 | +1 | `OK` |
| ts_007 | 9 / 9 | +0 | `OK` | 9 / 9 | +0 | `OK` |
| ts_010 | 9 / 10 | +1 | `OK` | 9 / 10 | +1 | `OK` |

## Detailed Analysis of Flagged Disagreements

## Disagreement Pattern Discovery
By comparing human comments with grader comments on flagged cases, we identify the following pattern:
- The AI Grader (v1) tends to give high marks (9s and 10s) based purely on correct factual content. It **overlooks robotic and awkwardly formatted advice** (such as "eligibility status of true" or "eligibility status is true").
- Human evaluation penalizes this phrasing because a real university advisor would never speak so mechanically to a prospective student. The human grader values natural phrasing and professional communication quality, resulting in a gap of 2-3 points in realism/helpfulness.
