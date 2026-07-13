import os
import sys
import json
import unittest

# Ensure root directory is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline import run_pipeline

class TestAdversarialRobustness(unittest.TestCase):
    def test_adversarial_cases(self):
        print("\n=== Running Adversarial Robustness Verification ===")
        
        cases = [
            {
                "name": "Typos in university name (LLM Fallback Picker)",
                "input": "I got 1010/1100 in Matric, 970/1100 in FSc, 185/200 in MDCAT. I want to apply to KIng EdWard U.",
                "expected_stage": "complete",
                "expected_uni": "King Edward Medical University"
            },
            {
                "name": "Marks written as word strings (Reader)",
                "input": "I got nine hundred and fifty marks in matric and eight hundred and eighty in fsc. My entry test ECAT score is two hundred and thirty. I want to go to UET Lahore.",
                "expected_stage": "complete",
                "expected_uni": "UET Lahore",
                "expected_merit": 74.84
            },
            {
                "name": "Conflicting exams for target university (Calculator graceful fail)",
                "input": "My Matric is 950/1100, FSc is 880/1100, MDCAT is 185. I want to apply to NUST.",
                "expected_stage": "failed_at_calculator",
                "expected_uni": "NUST"
            },
            {
                "name": "Ambiguous university name query",
                "input": "Matric 980/1100, FSc 940/1100, NET 142/200. I want to apply to the main medical college.",
                "expected_stage": "failed_at_formula_picker",
                "expected_uni": None
            }
        ]
        
        passed_cases = 0
        for c in cases:
            print(f"Testing: {c['name']}...")
            try:
                state = run_pipeline(c["input"])
                actual_stage = state.get("stage")
                actual_uni = state.get("university_matched")
                actual_merit = state.get("merit_score")
                
                stage_match = actual_stage == c["expected_stage"]
                uni_match = actual_uni == c["expected_uni"]
                
                merit_match = True
                if c.get("expected_merit") is not None:
                    merit_match = abs((actual_merit or 0) - c["expected_merit"]) <= 0.05
                    
                if stage_match and uni_match and merit_match:
                    print("  -> PASS")
                    passed_cases += 1
                else:
                    print(f"  -> FAIL: Stage={actual_stage} (expected {c['expected_stage']}), Uni={actual_uni} (expected {c['expected_uni']}), Merit={actual_merit}")
            except Exception as e:
                print(f"  -> ERROR (crashed): {e}")
                
        accuracy = (passed_cases / len(cases) * 100) if cases else 0
        print(f"\nAdversarial Robustness Accuracy: {accuracy:.1f}%\n")
        self.assertGreaterEqual(accuracy, 75.0, "Adversarial robustness check failed.")

if __name__ == "__main__":
    unittest.main()
