# Test Results - Day 7

## Execution Metadata
- **Test Run Timestamp**: `2026-07-11T12:02:12+05:00`
- **Pipeline Version**: `v3`
- **Reference Data Status**: Frozen against `data/formulas.json` (July 11, 2026, version `v3`)

## Test Student Results Grid

| Student ID | Description | Expected Stage | Actual Stage | Stage Check | Formula Check | Score Check | Eligibility Check |
|---|---|---|---|---|---|---|---|
| ts_001 | Normal KEMU applicant | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_002 | Normal NUST applicant | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_003 | Normal UET Lahore applicant | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_004 | NUST applicant just below the 50% cutoff | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_005 | NUST applicant just above the 50% cutoff | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_006 | Clearly ineligible KEMU applicant | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_007 | NUST applicant with standard totals fallback and ignored extra subject | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |
| ts_008 | Applicant applying to an unmatched university | `failed_at_formula_picker` | `failed_at_formula_picker` | `PASS` | `N/A` | `N/A` | `N/A` |
| ts_009 | KEMU applicant missing required entry exam score | `failed_at_calculator` | `failed_at_calculator` | `PASS` | `N/A` | `N/A` | `N/A` |
| ts_010 | Perfect scores KEMU applicant | `complete` | `complete` | `PASS` | `PASS` | `PASS` | `PASS` |

## Coverage Summary
- **Students Tested**: 10
- **Passed (all criteria)**: 10
- **Failed (at least one criterion)**: 0
- **Pipeline Errors**: 0
- **Accuracy**: 100.0%
