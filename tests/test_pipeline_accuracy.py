import os
import sys
import json
import time
import unittest
from datetime import datetime

# Ensure root directory is in path for imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline import run_pipeline

class TestPipelineAccuracy(unittest.TestCase):
    results = []
    test_students = []

    @classmethod
    def setUpClass(cls):
        # Load test students JSON from data folder
        students_path = os.path.join(root_dir, "data", "test_students.json")
        try:
            with open(students_path, "r", encoding="utf-8") as f:
                cls.test_students = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load test students from {students_path}: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        # Generate and write the results report
        cls.write_results_report()

    def run_student_test(self, student_id: str):
        # Find the student record
        student = next((s for s in self.test_students if s["id"] == student_id), None)
        if not student:
            self.fail(f"Student record with ID {student_id} not found in test dataset.")

        expected = student["expected"]
        actual_stage = None
        pipeline_error = None
        state = {}

        # 1. Run student input through the real pipeline
        try:
            state = run_pipeline(student["raw_input"])
            actual_stage = state.get("stage")
        except Exception as e:
            actual_stage = "CRASHED"
            pipeline_error = f"{type(e).__name__}: {str(e)}"

        # 2. Initialize results record (default N/A for criteria checks)
        record = {
            "id": student_id,
            "description": student["description"],
            "expected_stage": expected["stage"],
            "actual_stage": actual_stage,
            "stage": "FAIL",
            "formula": "N/A",
            "score": "N/A",
            "eligibility": "N/A",
            "error_msg": pipeline_error
        }

        # 3. Handle pipeline crash (ERROR)
        if pipeline_error:
            record["stage"] = "ERROR"
            record["formula"] = "ERROR"
            record["score"] = "ERROR"
            record["eligibility"] = "ERROR"
            self.results.append(record)
            self.fail(f"Pipeline crashed for student {student_id}: {pipeline_error}")

        # 4. Handle stage mismatch (FAIL)
        if actual_stage != expected["stage"]:
            record["stage"] = "FAIL"
            self.results.append(record)
            self.assertEqual(actual_stage, expected["stage"], f"Stage mismatch for {student_id}")

        record["stage"] = "PASS"

        # 5. Assertions on completed outcomes
        if expected["stage"] == "complete":
            # Compare formula details (matched university & display)
            act_uni = state.get("university_matched")
            act_display = state.get("intermediate_outputs", {}).get("formula_picker", {}).get("output", {}).get("formula_display")
            
            exp_uni = expected["university_matched"]
            exp_display = expected["formula_display"]
            
            formula_pass = (act_uni == exp_uni) and (act_display == exp_display)
            record["formula"] = "PASS" if formula_pass else "FAIL"
            
            # Compare merit score percentage (absolute tolerance ±0.01%)
            act_score = state.get("merit_score")
            exp_score = expected["merit_score"]
            score_pass = abs((act_score or 0) - (exp_score or 0)) <= 0.01
            record["score"] = "PASS" if score_pass else "FAIL"
            
            # Compare eligibility boolean
            act_elig = state.get("eligibility")
            exp_elig = expected["eligibility"]
            elig_pass = (act_elig == exp_elig)
            record["eligibility"] = "PASS" if elig_pass else "FAIL"
            
            # Save record before executing unittest asserts to guarantee logging even if assertion fails
            self.results.append(record)
            
            self.assertEqual(act_uni, exp_uni, f"Matched university mismatch: expected {exp_uni}, got {act_uni}")
            self.assertEqual(act_display, exp_display, f"Formula display mismatch: expected {exp_display}, got {act_display}")
            self.assertAlmostEqual(act_score, exp_score, delta=0.01, msg=f"Merit score mismatch: expected {exp_score}, got {act_score}")
            self.assertEqual(act_elig, exp_elig, f"Eligibility status mismatch: expected {exp_elig}, got {act_elig}")
        else:
            # If it's a failed_at_* stage, matching the stage is sufficient
            self.results.append(record)

    # Dynamic Test Cases Mapping
    def test_ts_001(self):
        self.run_student_test("ts_001")

    def test_ts_002(self):
        self.run_student_test("ts_002")

    def test_ts_003(self):
        self.run_student_test("ts_003")

    def test_ts_004(self):
        self.run_student_test("ts_004")

    def test_ts_005(self):
        self.run_student_test("ts_005")

    def test_ts_006(self):
        self.run_student_test("ts_006")

    def test_ts_007(self):
        self.run_student_test("ts_007")

    def test_ts_008(self):
        self.run_student_test("ts_008")

    def test_ts_009(self):
        self.run_student_test("ts_009")

    def test_ts_010(self):
        self.run_student_test("ts_010")

    def test_ts_011(self):
        self.run_student_test("ts_011")

    def test_ts_012(self):
        self.run_student_test("ts_012")

    @classmethod
    def write_results_report(cls):
        # Create reports directory if missing
        reports_dir = os.path.join(root_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, "test_results_day7.md")
        
        # Calculate statistics
        total = len(cls.results)
        passed = 0
        failed = 0
        errors = 0
        
        for r in cls.results:
            if any(f == "ERROR" for f in [r["stage"], r["formula"], r["score"], r["eligibility"]]):
                errors += 1
            elif any(f == "FAIL" for f in [r["stage"], r["formula"], r["score"], r["eligibility"]]):
                failed += 1
            else:
                passed += 1
                
        accuracy = (passed / total * 100) if total > 0 else 0
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+05:00"
        
        # Check if file exists to read previous contents
        previous_content = ""
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    previous_content = f.read()
            except Exception as e:
                print(f"Failed to read existing report: {e}")

        # Check if we should append as a follow-up run
        is_followup = "Test Results - Day 7" in previous_content
        
        run_title = "Test Results - Day 7" if not is_followup else f"Follow-up Run (Extra 1 - FAST NUCES Integration) - {timestamp}"
        
        report_segment = f"""
# {run_title}

## Execution Metadata
- **Test Run Timestamp**: `{timestamp}`
- **Pipeline Version**: `v3`
- **Reference Data Status**: Frozen against `data/formulas.json` (July 11, 2026, version `v3`)

## Test Student Results Grid

| Student ID | Description | Expected Stage | Actual Stage | Stage Check | Formula Check | Score Check | Eligibility Check |
|---|---|---|---|---|---|---|---|
"""
        sorted_results = sorted(cls.results, key=lambda x: x["id"])
        for r in sorted_results:
            report_segment += f"| {r['id']} | {r['description']} | `{r['expected_stage']}` | `{r['actual_stage']}` | `{r['stage']}` | `{r['formula']}` | `{r['score']}` | `{r['eligibility']}` |\n"
            
        report_segment += f"""
## Coverage Summary
- **Students Tested**: {total}
- **Passed (all criteria)**: {passed}
- **Failed (at least one criterion)**: {failed}
- **Pipeline Errors**: {errors}
- **Accuracy**: {accuracy:.1f}%
"""
        if is_followup:
            final_content = previous_content.strip() + "\n\n---\n" + report_segment
        else:
            final_content = report_segment

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print(f"\n--- {run_title} Summary ---")
        print(f"Total Students: {total}")
        print(f"Passed (all criteria): {passed}")
        print(f"Failed (at least one criterion): {failed}")
        print(f"Pipeline Errors: {errors}")
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"Detailed Markdown report updated in: {report_path}\n")

if __name__ == "__main__":
    unittest.main()
