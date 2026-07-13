import os
import json
import sys
import time
import hashlib
from datetime import datetime

# Ensure directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import config
from state import create_initial_state
from agents.reader import run_reader
from agents.formula_picker import pick_formula
from tools.calculator import calculate_merit
from agents.advisor import run_advisor
from agents.checker import run_checker

def load_standard_totals() -> dict:
    """Loads fallback denominators from data/formulas.json."""
    formulas_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "formulas.json")
    try:
        with open(formulas_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("standard_totals", {})
    except Exception as e:
        print(f"Failed to load standard totals: {str(e)}")
        return {}

def get_cache_key(university_matched: str, marks: dict) -> str:
    """Generates a stable, sorted SHA-256 hash for parsed profile and matched university."""
    sorted_marks = {}
    if marks:
        for k in sorted(marks.keys()):
            val = marks[k]
            if isinstance(val, dict):
                sorted_marks[k] = {subkey: val[subkey] for subkey in sorted(val.keys())}
            else:
                sorted_marks[k] = val
    key_data = {
        "university_matched": university_matched or "",
        "marks": sorted_marks
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

def load_cache() -> dict:
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "memory_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data: dict):
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "memory_cache.json")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Failed to save memory cache: {e}")

def get_next_run_filepath() -> str:
    """Determines next run_XXX.json filepath."""
    os.makedirs("runs", exist_ok=True)
    counter = 1
    while True:
        filename = f"run_{counter:03d}.json"
        filepath = os.path.join("runs", filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1

def save_run_record(state: dict) -> str:
    """Saves the pipeline state to runs/run_XXX.json."""
    run_filepath = get_next_run_filepath()
    filename = os.path.basename(run_filepath)
    state["run_file"] = filename
    run_record = {
        "student_input": state["student_input"],
        "state": state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "pipeline_version": state["pipeline_version"]
    }
    try:
        with open(run_filepath, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2)
        print(f"Run saved successfully to {run_filepath}")
        return filename
    except Exception as e:
        print(f"Failed to write run record to {run_filepath}: {str(e)}")
        return ""

def run_pipeline(student_input: str, bypass_cache: bool = False) -> dict:
    """
    Executes the multi-agent pipeline with quality checking and rewrite capabilities:
    Reader -> Formula Picker -> Calculator -> Advisor -> Checker -> (Advisor Rewrite -> Checker)
    Tracks stage durations and handles failures.
    """
    state = create_initial_state(student_input)
    
    # 1. Reader
    state["stage"] = "reader"
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
        if not profile and not state["errors"]:
            state["errors"].append("Reader returned empty profile.")
        save_run_record(state)
        return state

    # 2. Formula Picker
    state["stage"] = "formula_picker"
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
        if not picker_result.get("found", False) and not state["errors"]:
            state["errors"].append(f"University '{profile.get('university_raw', '')}' could not be matched.")
        save_run_record(state)
        return state

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
            print(f"[OK] Cache Hit! Loaded pre-calculated result (from {entry.get('cached_from_run', 'unknown')}).")
            save_run_record(state)
            return state

    # 3. Calculator
    state["stage"] = "calculator"
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
        save_run_record(state)
        return state
        
    state["merit_score"] = calc_result["merit_score"]
    state["eligibility"] = calc_result["eligibility"]

    # 4. Advisor Attempt 1
    state["stage"] = "advisor"
    start_time = time.perf_counter()
    advisor_result = run_advisor(profile, state["formula"], state["merit_score"], state["eligibility"], state)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Check for DELIBERATE_REJECTION hook to mock the advisor's first output
    if "DELIBERATE_REJECTION" in student_input:
        advisor_result = {
            "advice": "Great news! You are fully eligible and are a highly competitive candidate for admission to King Edward Medical University with your marks. You will easily get in!"
        }
        state["advice"] = advisor_result["advice"]
        print("[MOCK INJECTION] Injected mock optimistic advice for DELIBERATE_REJECTION test case.")

    state["intermediate_outputs"]["advisor_attempt_1"] = {
        "duration_ms": duration_ms,
        "output": advisor_result
    }
    
    if state["errors"] or not advisor_result:
        state["stage"] = "failed_at_advisor"
        if not advisor_result and not state["errors"]:
            state["errors"].append("Advisor returned empty advice on attempt 1.")
        save_run_record(state)
        return state

    # 5. Checker Attempt 1
    state["stage"] = "checker"
    start_time = time.perf_counter()
    checker_result = run_checker(state["merit_score"], state["eligibility"], state["advice"], state)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    state["checker_verdict"] = checker_result
    state["intermediate_outputs"]["checker_attempt_1"] = {
        "duration_ms": duration_ms,
        "output": checker_result
    }
    
    if checker_result.get("approved") is None:
        # Checker execution or parsing failed
        state["stage"] = "failed_at_checker"
        save_run_record(state)
        return state

    # Check approval status
    if checker_result.get("approved") is True:
        state["stage"] = "complete"
        save_run_record(state)
        return state

    # 6. Quality Loop Rewrite (Attempt 2)
    # Reference config.MAX_REWRITES instead of hardcoding
    if config.MAX_REWRITES >= 1:
        print(f"Advice rejected. Triggering rewrite loop (1/{config.MAX_REWRITES}) due to: {checker_result.get('reason')}")
        
        state["stage"] = "advisor_rewrite"
        start_time = time.perf_counter()
        # Structured payload contains previous advice and checker feedback
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
        
        # Log Advisor Attempt 2
        state["intermediate_outputs"]["advisor_attempt_2"] = {
            "duration_ms": duration_ms,
            "output": rewrite_advisor_result
        }
        state["rewrite_count"] = 1
        
        # Fallback if rewrite Advisor call failed
        if state["errors"] or not rewrite_advisor_result:
            print("Advisor rewrite failed. Falling back to original advice.")
            state["advice"] = advisor_result.get("advice", "")
            # We clear errors that occurred during rewrite so we can save a clean run
            state["errors"] = [e for e in state["errors"] if "Advisor" not in e]
            state["stage"] = "complete"
            save_run_record(state)
            return state

        # 7. Checker Attempt 2
        state["stage"] = "checker_rewrite"
        start_time = time.perf_counter()
        second_checker_result = run_checker(state["merit_score"], state["eligibility"], state["advice"], state)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        state["checker_verdict"] = second_checker_result
        state["intermediate_outputs"]["checker_attempt_2"] = {
            "duration_ms": duration_ms,
            "output": second_checker_result
        }
        
        if second_checker_result.get("approved") is None:
            # Second checker execution/parsing failed
            state["stage"] = "failed_at_checker"
            save_run_record(state)
            return state

    # Final complete state (even if still rejected, stage="complete", checker_verdict contains the False approval status)
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
        
    return state
