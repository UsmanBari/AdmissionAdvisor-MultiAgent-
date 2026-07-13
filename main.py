import os
import sys
import argparse

# Ensure directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import run_pipeline

TEST_CASES = [
    # 1. KEMU normal student
    "I got 1010/1100 in Matric, 970/1100 in FSc and 185 in MDCAT. I want to apply to King Edward Medical University.",
    # 2. NUST student
    "My marks are Matric: 980/1100, FSc: 940/1100, and NET (NUST Entry Test): 142/200. I want to apply to NUST for computer science.",
    # 3. UET Lahore student
    "Hello, I got 950 marks in Matric, 880 in FSc and my ECAT score is 230 out of 400. Can I get admission in UET Lahore?",
    # 4. Obscure/Less common university
    "I scored 850 in Matric and 810 in FSc. I didn't take any entrance test. I want to apply to Greenwood Institute of Science and Technology for BS IT.",
    # 5. Edge case: perfect marks
    "I have 1100/1100 in Matric, 1100/1100 in FSc, and 200/200 in MDCAT. I want to apply to King Edward Medical University.",
    # 6. Edge case: very low marks
    "I got 450/1100 in Matric, 400/1100 in FSc, and 30/200 in MDCAT. Can I get admission in King Edward Medical University?",
    # 7. Edge case: missing entrance exam score
    "I got 1020 in Matric, 990 in FSc, but I couldn't attend the MDCAT exam. I want to apply to King Edward Medical University.",
    # 8. DELIBERATE REJECTION: Low marks student with a mock optimistic Advisor (guarantees rejection + rewrite loop test)
    "DELIBERATE_REJECTION: I got 450/1100 in Matric, 400/1100 in FSc, and 30/200 in MDCAT. Can I get admission in King Edward Medical University?"
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cache", action="store_true", help="Bypass the memory cache entirely")
    args = parser.parse_args()

    print(f"Starting {len(TEST_CASES)} pipeline test runs...\n")
    
    for idx, test_input in enumerate(TEST_CASES, 1):
        print(f"--- Running Test Case {idx} ---")
        print(f"Input: {test_input}")
        
        # Run pipeline
        state = run_pipeline(test_input, bypass_cache=args.no_cache)
        
        # Display output
        print(f"Stage: {state.get('stage')}")
        print(f"Merit Score: {state.get('merit_score')}")
        print(f"Eligibility: {state.get('eligibility')}")
        print(f"Checker Verdict Approved: {state.get('checker_verdict', {}).get('approved')}")
        print(f"Checker Reason: {state.get('checker_verdict', {}).get('reason')}")
        print(f"Rewrite Count: {state.get('rewrite_count')}")
        print(f"Advice: {state.get('advice')}")
        if state.get("errors"):
            print(f"Errors: {state['errors']}")
        print(f"---------------------------------\n")

if __name__ == "__main__":
    main()
