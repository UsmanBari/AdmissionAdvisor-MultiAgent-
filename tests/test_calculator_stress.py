import os
import sys
import json

# Ensure parent directory is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from tools.calculator import calculate_merit

TEST_CASES = {
    "mark_of_zero": {
        "marks": {
            "matric": {"obtained": 0, "total": 1100},
            "fsc": {"obtained": 800, "total": 1100}
        },
        "formula": {"matric": 0.50, "fsc": 0.50},
        "standard_totals": {"matric": 1100, "fsc": 1100}
    },
    "mark_higher_than_total": {
        "marks": {
            "matric": {"obtained": 1200, "total": 1100},
            "fsc": {"obtained": 800, "total": 1100}
        },
        "formula": {"matric": 0.50, "fsc": 0.50},
        "standard_totals": {"matric": 1100, "fsc": 1100}
    },
    "negative_mark": {
        "marks": {
            "matric": {"obtained": -50, "total": 1100},
            "fsc": {"obtained": 800, "total": 1100}
        },
        "formula": {"matric": 0.50, "fsc": 0.50},
        "standard_totals": {"matric": 1100, "fsc": 1100}
    },
    "total_of_zero": {
        "marks": {
            "matric": {"obtained": 900, "total": 0},
            "fsc": {"obtained": 800, "total": 1100}
        },
        "formula": {"matric": 0.50, "fsc": 0.50},
        "standard_totals": {"matric": 1100, "fsc": 1100}
    },
    "exact_cutoff_boundary": {
        "marks": {
            "matric": {"obtained": 550, "total": 1100}
        },
        "formula": {"matric": 1.0},
        "standard_totals": {"matric": 1100}
    },
    "non_sum_one_weights": {
        "marks": {
            "matric": {"obtained": 1100, "total": 1100},
            "fsc": {"obtained": 1100, "total": 1100}
        },
        "formula": {"matric": 0.5, "fsc": 0.3},
        "standard_totals": {"matric": 1100, "fsc": 1100}
    }
}

def run_tests():
    print("==================================================")
    print("RUNNING CALCULATOR STRESS TESTS IN ISOLATION")
    print("==================================================")
    
    results = {}
    for name, params in TEST_CASES.items():
        print(f"\n--- Test Case: {name} ---")
        print(f"Marks Input: {params['marks']}")
        print(f"Formula: {params['formula']}")
        
        crashed = False
        output = None
        
        try:
            output = calculate_merit(params["marks"], params["formula"], params["standard_totals"])
        except Exception as e:
            crashed = True
            output = f"CRASHED: {type(e).__name__}: {str(e)}"
            
        print(f"Output: {json.dumps(output, indent=2)}")
        
        results[name] = {
            "params": params,
            "output": output,
            "crashed": crashed
        }
        
    # Write results to reports for reference
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "calculator_stress_raw.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_tests()
