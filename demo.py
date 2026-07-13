import os
import sys
import json
import time
import argparse
from datetime import datetime

# Ensure root directory is in path for imports
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import config
from state import create_initial_state
from agents.reader import run_reader
from agents.formula_picker import pick_formula
from tools.calculator import calculate_merit
from agents.advisor import run_advisor
from agents.checker import run_checker
from pipeline import load_standard_totals, save_run_record, get_cache_key, load_cache, save_cache

def print_separator(char="=", length=60):
    print("\n" + char * length)

def run_interactive_pipeline(student_input: str, bypass_cache: bool = False):
    print_separator("=")
    print(f"INPUT: '{student_input}'")
    print_separator("=")
    
    state = create_initial_state(student_input)
    
    # 1. Reader
    print("\nSTAGE 1: [Reader] -> Extracting profile info...")
    start_time = time.perf_counter()
    profile = run_reader(student_input, state)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    state["student_profile"] = profile
    state["intermediate_outputs"]["reader"] = {
        "duration_ms": duration_ms,
        "output": profile
    }
    
    if state["errors"] or not profile:
        state["stage"] = "failed_at_reader"
        print(f"[FAIL] [Reader] Failed. Errors logged: {state['errors']}")
        save_run_record(state)
        return
        
    print(f"[OK] [Reader] Extraction complete ({duration_ms} ms):")
    print("  Extracted Marks:")
    for subj, marks in profile.get("marks", {}).items():
        if marks.get("obtained") is not None:
            print(f"    - {subj.upper()}: {marks['obtained']}/{marks.get('total') or 'standard'}")
    print(f"  Target University Raw: '{profile.get('university_raw')}'")
    
    # 2. Formula Picker
    print("\nSTAGE 2: [Formula Picker] -> Matching university weights...")
    start_time = time.perf_counter()
    picker_result = pick_formula(profile.get("university_raw", ""), state)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    state["formula"] = picker_result.get("formula", {})
    state["university_matched"] = picker_result.get("matched_university", None)
    state["intermediate_outputs"]["formula_picker"] = {
        "duration_ms": duration_ms,
        "output": picker_result
    }
    
    if state["errors"] or not picker_result.get("found", False):
        state["stage"] = "failed_at_formula_picker"
        print(f"[FAIL] [Formula Picker] Failed. University '{profile.get('university_raw')}' is not registered.")
        save_run_record(state)
        return
        
    print(f"[OK] [Formula Picker] Match success ({duration_ms} ms):")
    print(f"  Matched Key: '{state['university_matched']}'")
    print(f"  Formula Display: '{picker_result.get('formula_display')}'")
    
    # Cache Check (placed after Reader and Picker but before Calculator/Advisor/Checker)
    cache_key = None
    if not bypass_cache:
        cache_key = get_cache_key(state["university_matched"], profile.get("marks", {}))
        cache = load_cache()
        if cache_key in cache:
            entry = cache[cache_key]
            state["merit_score"] = entry["merit_score"]
            state["eligibility"] = entry["eligibility"]
            state["advice"] = entry["advice"]
            state["checker_verdict"] = entry["checker_verdict"]
            state["cache_hit"] = True
            state["stage"] = "complete"
            print(f"\n[OK] Cache Hit! Skipping Calculator, Advisor, and Checker.")
            print(f"  Loaded pre-calculated result (from {entry.get('cached_from_run', 'unknown')}).")
            save_run_record(state)
            
            # Print Final Summary immediately
            print_separator("-")
            print("FINAL SUMMARY REPORT (FROM CACHE)")
            print_separator("-")
            print(f"Stage Status: {state['stage']}")
            print(f"University Matched: {state['university_matched']}")
            print(f"Merit Score: {state['merit_score']:.2f}%")
            print(f"Eligibility: {state['eligibility']}")
            print(f"Advice:\n\"{state['advice']}\"")
            print_separator("=")
            return
    
    # 3. Calculator
    print("\nSTAGE 3: [Calculator] -> Running deterministic code calculations...")
    start_time = time.perf_counter()
    standard_totals = load_standard_totals()
    calc_result = calculate_merit(profile.get("marks", {}), state["formula"], standard_totals)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    state["intermediate_outputs"]["calculator"] = {
        "duration_ms": duration_ms,
        "output": calc_result
    }
    
    if calc_result.get("error"):
        state["errors"].append(calc_result["error"])
        state["stage"] = "failed_at_calculator"
        print(f"[FAIL] [Calculator] Failed: {calc_result['error']}")
        save_run_record(state)
        return
        
    state["merit_score"] = calc_result["merit_score"]
    state["eligibility"] = calc_result["eligibility"]
    
    print(f"[OK] [Calculator] Evaluation success ({duration_ms} ms):")
    print(f"  Computed Merit Score: {state['merit_score']:.2f}%")
    print(f"  Eligibility Status: {'ELIGIBLE' if state['eligibility'] else 'INELIGIBLE'}")
    
    # 4. Advisor Attempt 1
    print("\nSTAGE 4: [Advisor] -> Generating admissions advice draft...")
    start_time = time.perf_counter()
    advisor_result = run_advisor(profile, state["formula"], state["merit_score"], state["eligibility"], state)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Check for DELIBERATE_REJECTION hook to mock the advisor's first output
    if "DELIBERATE_REJECTION" in student_input:
        advisor_result = {
            "advice": "Great news! You are fully eligible and are a highly competitive candidate for admission to King Edward Medical University with your marks. You will easily get in!"
        }
        state["advice"] = advisor_result["advice"]
        print("[WARN] [MOCK INJECTION] Mock optimistic advice loaded for testing rewrite flow.")
        
    state["intermediate_outputs"]["advisor_attempt_1"] = {
        "duration_ms": duration_ms,
        "output": advisor_result
    }
    
    if state["errors"] or not advisor_result:
        state["stage"] = "failed_at_advisor"
        print(f"[FAIL] [Advisor] Failed. Errors logged: {state['errors']}")
        save_run_record(state)
        return
        
    print(f"[OK] [Advisor] Draft generated ({duration_ms} ms):")
    print(f"  Advice: \"{state['advice']}\"")
    
    # 5. Checker Attempt 1
    print("\nSTAGE 5: [Checker] -> Auditing advice draft against score...")
    start_time = time.perf_counter()
    checker_result = run_checker(state["merit_score"], state["eligibility"], state["advice"], state)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    state["checker_verdict"] = checker_result
    state["intermediate_outputs"]["checker_attempt_1"] = {
        "duration_ms": duration_ms,
        "output": checker_result
    }
    
    if checker_result.get("approved") is None:
        state["stage"] = "failed_at_checker"
        print(f"[FAIL] [Checker] Failed to run audit check.")
        save_run_record(state)
        return
        
    if checker_result.get("approved") is True:
        state["stage"] = "complete"
        print(f"[OK] [Checker] Approved draft ({duration_ms} ms).")
        save_run_record(state)
        return
        
    print(f"[WARN] [Checker] REJECTED draft ({duration_ms} ms). Reason: {checker_result.get('reason')}")
    
    # 6. Advisor Attempt 2 (Rewrite)
    if config.MAX_REWRITES >= 1:
        print("\nSTAGE 6: [Advisor Rewrite] -> Revising advice per feedback...")
        start_time = time.perf_counter()
        rewrite_advisor_result = run_advisor(
            profile=profile,
            formula=state["formula"],
            merit_score=state["merit_score"],
            eligibility=state["eligibility"],
            state=state,
            previous_advice=state["advice"],
            checker_feedback=checker_result.get("reason", "")
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        state["intermediate_outputs"]["advisor_attempt_2"] = {
            "duration_ms": duration_ms,
            "output": rewrite_advisor_result
        }
        state["rewrite_count"] = 1
        
        if state["errors"] or not rewrite_advisor_result:
            print("[FAIL] [Advisor Rewrite] Failed. Falling back to original advice.")
            state["advice"] = advisor_result.get("advice", "")
            state["errors"] = [e for e in state["errors"] if "Advisor" not in e]
            state["stage"] = "complete"
            save_run_record(state)
            return
            
        print(f"[OK] [Advisor] Revised advice generated ({duration_ms} ms):")
        print(f"  Advice: \"{state['advice']}\"")
        
        # 7. Checker Attempt 2
        print("\nSTAGE 7: [Checker Rewrite] -> Auditing revised draft...")
        start_time = time.perf_counter()
        second_checker_result = run_checker(state["merit_score"], state["eligibility"], state["advice"], state)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        state["checker_verdict"] = second_checker_result
        state["intermediate_outputs"]["checker_attempt_2"] = {
            "duration_ms": duration_ms,
            "output": second_checker_result
        }
        
        if second_checker_result.get("approved") is None:
            state["stage"] = "failed_at_checker"
            print("[FAIL] [Checker Rewrite] Failed to run audit check.")
            save_run_record(state)
            return
            
        if second_checker_result.get("approved") is True:
            print(f"[OK] [Checker] Approved revised draft ({duration_ms} ms).")
        else:
            print(f"[WARN] [Checker] Second draft rejected. Proceeding anyway.")
            
    state["stage"] = "complete"
    run_file = save_run_record(state)
    
    # Save to cache if complete and not a cache hit and cache_key is available
    if not state.get("cache_hit") and cache_key:
        cache = load_cache()
        cache[cache_key] = {
            "university_matched": state["university_matched"],
            "marks": profile.get("marks", {}),
            "merit_score": state["merit_score"],
            "eligibility": state["eligibility"],
            "advice": state["advice"],
            "checker_verdict": state["checker_verdict"],
            "cached_from_run": run_file,
            "cached_at": datetime.utcnow().isoformat() + "Z"
        }
        save_cache(cache)
        
    print_separator("-")
    print("FINAL SUMMARY REPORT")
    print_separator("-")
    print(f"Stage Status: {state['stage']}")
    print(f"University Matched: {state['university_matched']}")
    print(f"Merit Score: {state['merit_score']:.2f}%")
    print(f"Eligibility: {state['eligibility']}")
    print(f"Advice:\n\"{state['advice']}\"")
    print_separator("=")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-broken", action="store_true", help="Deliberately trigger the checker rejection loop demo")
    parser.add_argument("--no-cache", action="store_true", help="Bypass the memory cache entirely")
    args = parser.parse_args()
    
    if args.demo_broken:
        student_input = "DELIBERATE_REJECTION: My marks are Matric: 980/1100, FSc: 940/1100, NET: 142/200. I want to apply to NUST."
        run_interactive_pipeline(student_input, bypass_cache=args.no_cache)
        return

    while True:
        print_separator("#", 60)
        print("    ADMISSION ADVISOR SYSTEM - MENTOR DEMO MODE    ")
        print_separator("#", 60)
        print("Select an option:")
        print("1. Enter custom student profile (interactive text input)")
        print("2. Run Demo: Fuzzy matching (picker fallback path for university typos)")
        print("3. Run Demo: Missing marks (graceful calculator block)")
        print("4. Run Demo: Unmatched university (picker failure path)")
        print("5. Run Demo: Checker audit rejection & rewrite loop (using debug hook)")
        print("6. Exit")
        
        choice = input("\nSelect choice (1-6): ").strip()
        
        if choice == "1":
            student_input = input("\nEnter student info (marks + university): ").strip()
            if student_input:
                run_interactive_pipeline(student_input, bypass_cache=args.no_cache)
        elif choice == "2":
            student_input = "I got 1010/1100 in Matric, 970/1100 in FSc, 185 in MDCAT. I want to apply to KIng EdWard U."
            run_interactive_pipeline(student_input, bypass_cache=args.no_cache)
        elif choice == "3":
            student_input = "I got 1020 in Matric, 990 in FSc, but I couldn't attend the MDCAT exam. I want to apply to King Edward Medical University."
            run_interactive_pipeline(student_input, bypass_cache=args.no_cache)
        elif choice == "4":
            student_input = "I scored 850 in Matric and 810 in FSc. I want to apply to Greenwood Institute of Science and Technology for BS IT."
            run_interactive_pipeline(student_input, bypass_cache=args.no_cache)
        elif choice == "5":
            student_input = "DELIBERATE_REJECTION: My marks are Matric: 980/1100, FSc: 940/1100, NET: 142/200. I want to apply to NUST."
            run_interactive_pipeline(student_input, bypass_cache=args.no_cache)
        elif choice == "6":
            print("\nExiting. Thank you!")
            break
        else:
            print("\nInvalid choice. Please select 1-6.")
            
        cont = input("\nRun another demonstration case? (y/n): ").strip().lower()
        if cont != 'y':
            print("\nExiting. Thank you!")
            break

if __name__ == "__main__":
    main()
