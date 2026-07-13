import os
import sys
import json
import unittest
from datetime import datetime

# Ensure root directory is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline import run_pipeline

class TestLLMStability(unittest.TestCase):
    def test_multi_run_consistency(self):
        print("\n=== Running LLM Stability Verification (3x Iterations) ===")
        # Load test cases
        students_path = os.path.join(root_dir, "data", "test_students.json")
        try:
            with open(students_path, "r", encoding="utf-8") as f:
                students = json.load(f)
        except Exception as e:
            self.fail(f"Failed to load test student list: {e}")
            
        runs_per_student = 3
        total_checks = 0
        consistent_checks = 0
        
        for s in students:
            # We only test cases that are expected to complete successfully
            if s["expected"]["stage"] != "complete":
                continue
                
            print(f"Testing stability for student {s['id']}...")
            raw_input = s["raw_input"]
            
            stages = []
            universities = []
            merits = []
            eligibilities = []
            
            for i in range(runs_per_student):
                try:
                    state = run_pipeline(raw_input)
                    stages.append(state.get("stage"))
                    universities.append(state.get("university_matched"))
                    merits.append(state.get("merit_score"))
                    eligibilities.append(state.get("eligibility"))
                except Exception as e:
                    stages.append("CRASHED")
                    universities.append(None)
                    merits.append(None)
                    eligibilities.append(None)
                    
            # Check consistency
            stage_consistent = len(set(stages)) == 1
            uni_consistent = len(set(universities)) == 1
            elig_consistent = len(set(eligibilities)) == 1
            
            if merits and all(m is not None for m in merits):
                merit_consistent = (max(merits) - min(merits)) <= 0.02
            else:
                merit_consistent = len(set(merits)) == 1
                
            total_checks += 4
            if stage_consistent: consistent_checks += 1
            if uni_consistent: consistent_checks += 1
            if merit_consistent: consistent_checks += 1
            if elig_consistent: consistent_checks += 1
            
            print(f"  - Stages: {stages} ({'CONSISTENT' if stage_consistent else 'VARIED'})")
            print(f"  - Matched Universities: {universities} ({'CONSISTENT' if uni_consistent else 'VARIED'})")
            print(f"  - Merit Scores: {merits} ({'CONSISTENT' if merit_consistent else 'VARIED'})")
            print(f"  - Eligibilities: {eligibilities} ({'CONSISTENT' if elig_consistent else 'VARIED'})")
            
        stability_rate = (consistent_checks / total_checks * 100) if total_checks > 0 else 0
        print(f"\nOverall LLM Stability Rate: {stability_rate:.1f}%\n")
        self.assertGreaterEqual(stability_rate, 80.0, "LLM stability is below acceptable threshold.")

if __name__ == "__main__":
    unittest.main()
