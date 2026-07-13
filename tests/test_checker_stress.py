import os
import sys
import json

# Ensure parent directory is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from agents.checker import run_checker

TEST_CASES = {
    "salesy_but_correct": {
        "merit_score": 90.7,
        "eligibility": True,
        "advice": "OMG! You are a superstar! You are 100% eligible for King Edward Medical University! Go celebrate! Your scores are absolutely phenomenal!"
    },
    "program_mismatch_low_merit": {
        "merit_score": 55.0,
        "eligibility": True,
        "advice": "You have met the eligibility criteria for admission. With a merit score of 55.00%, you are eligible and should apply for King Edward Medical University's open merit seats. We highly recommend you go for KEMU as you are guaranteed to have a competitive chance."
    },
    "low_effort_advice": {
        "merit_score": 75.0,
        "eligibility": True,
        "advice": "You're eligible. Good luck."
    },
    "cutoff_boundary_false_confidence": {
        "merit_score": 50.1,
        "eligibility": True,
        "advice": "Congratulations! You have scored 50.10% merit. You are fully eligible for NUST and you have an excellent, guaranteed chance of being selected for their computer science program."
    }
}

def run_tests():
    print("==================================================")
    print("RUNNING CHECKER STRESS TESTS IN ISOLATION")
    print("==================================================")
    
    results = {}
    for name, params in TEST_CASES.items():
        print(f"\n--- Test Case: {name} ---")
        print(f"Merit Score: {params['merit_score']}")
        print(f"Eligibility: {params['eligibility']}")
        print(f"Advice: '{params['advice']}'")
        
        state = {"errors": []}
        crashed = False
        output = None
        
        try:
            output = run_checker(params["merit_score"], params["eligibility"], params["advice"], state)
        except Exception as e:
            crashed = True
            output = f"CRASHED: {type(e).__name__}: {str(e)}"
            
        print(f"Output: {json.dumps(output, indent=2)}")
        print(f"State errors: {state['errors']}")
        
        results[name] = {
            "params": params,
            "output": output,
            "errors": state["errors"],
            "crashed": crashed
        }
        
    # Write results to reports for reference
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "checker_stress_raw.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_tests()
