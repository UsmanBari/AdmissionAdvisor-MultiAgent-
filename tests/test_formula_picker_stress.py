import os
import sys
import json

# Ensure parent directory is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from agents.formula_picker import pick_formula

TEST_CASES = {
    "ambiguous_substring": "Lahore",
    "empty_string": "",
    "spacing_and_casing": "   kEmU   ",
    "multiple_universities": "KEMU or NUST",
    "fictional_university": "Hogwarts School of Witchcraft and Wizardry"
}

def run_tests():
    print("==================================================")
    print("RUNNING FORMULA PICKER STRESS TESTS IN ISOLATION")
    print("==================================================")
    
    results = {}
    for name, text in TEST_CASES.items():
        print(f"\n--- Test Case: {name} ---")
        print(f"Input Raw University: '{text}'")
        
        state = {"errors": [], "formula": {}}
        crashed = False
        output = None
        
        try:
            output = pick_formula(text, state)
        except Exception as e:
            crashed = True
            output = f"CRASHED: {type(e).__name__}: {str(e)}"
            
        print(f"Output: {json.dumps(output, indent=2)}")
        print(f"State errors: {state['errors']}")
        
        results[name] = {
            "input": text,
            "output": output,
            "errors": state["errors"],
            "crashed": crashed
        }
        
    # Write results to reports for reference
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "formula_picker_stress_raw.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_tests()
