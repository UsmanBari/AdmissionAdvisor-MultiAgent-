import os
import sys
import json

# Ensure parent directory is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from agents.reader import run_reader

TEST_CASES = {
    "garbled_nonsense": "alkjfdskfjhasdkjfh",
    "numbers_no_context": "970 1010 185",
    "conflicting_universities": "I want to apply to KEMU. My FSC is 1000 and Matric is 950. Also I want to apply to NUST where my FSC is 980 and Matric is 940, and to UET with FSC 900.",
    "mixed_urdu_english": "Mera FSC me 980 marks hain aur matric me 1010. MDCAT nahi diya. KEMU me apply karna chahta hu.",
    "impossible_overflow_values": "I got 5000 in matric, 4500 in FSC. I want to apply to King Edward.",
    "empty_whitespace": "   ",
    "contradictory_same_subject": "I got 950 in FSC but my FSC score is actually 920. KEMU is the university."
}

def run_tests():
    print("==================================================")
    print("RUNNING READER STRESS TESTS IN ISOLATION")
    print("==================================================")
    
    results = {}
    for name, text in TEST_CASES.items():
        print(f"\n--- Test Case: {name} ---")
        print(f"Input: '{text}'")
        
        state = {"errors": [], "student_profile": {}}
        crashed = False
        output = None
        
        try:
            output = run_reader(text, state)
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
    with open(os.path.join(reports_dir, "reader_stress_raw.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_tests()
