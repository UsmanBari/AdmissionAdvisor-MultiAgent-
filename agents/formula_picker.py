import os
import json
import sys

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from llm import LLMService

def normalize_name(name: str) -> str:
    """Helper to strip whitespace and lowercase for comparison."""
    if not name:
        return ""
    return "".join(name.lower().split())

def pick_formula(university_raw: str, state: dict = None) -> dict:
    """
    Attempts to match raw university name with official names or aliases.
    Uses code-only lookup first, then falls back to fuzzy match via LLM.
    Writes to state["formula"] and logs errors if not found.
    """
    # Initialize return dictionary
    result = {
        "formula": {},
        "formula_display": "",
        "found": False,
        "matched_university": None
    }

    # Load formulas.json
    formulas_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "formulas.json")
    try:
        with open(formulas_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            universities_data = data.get("universities", {})
    except Exception as e:
        error_msg = f"Formula picker failed to load formulas.json: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return result

    # 1. Try direct/alias code-only match
    norm_raw = normalize_name(university_raw)
    matched_key = None
    
    for uni_name, uni_info in universities_data.items():
        # Check against official name
        if norm_raw == normalize_name(uni_name):
            matched_key = uni_name
            break
        # Check against aliases
        aliases = [normalize_name(a) for a in uni_info.get("aliases", [])]
        if norm_raw in aliases:
            matched_key = uni_name
            break

    if matched_key:
        matched_info = universities_data[matched_key]
        result["formula"] = matched_info.get("formula", {})
        result["formula_display"] = matched_info.get("formula_display", "")
        result["found"] = True
        result["matched_university"] = matched_key
        if state is not None:
            state["formula"] = result["formula"]
        return result

    # 2. Fall back to LLM for fuzzy matching (only if code-only match fails)
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "formula_picker_fallback_v1.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except Exception as e:
        error_msg = f"Formula picker fallback failed to load system prompt: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return result

    official_names = list(universities_data.keys())
    context = {
        "official_universities": official_names
    }

    try:
        response_text = LLMService.ask(
            system_prompt=system_prompt,
            user_input=f"Fuzzy match this university name: '{university_raw}'",
            context=context,
            system_prompt_name="prompts/formula_picker_fallback_v1.md"
        )
    except Exception as e:
        error_msg = f"Formula picker fallback LLM call failed: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return result

    try:
        parsed = json.loads(response_text.strip())
        found = parsed.get("found", False)
        matched_uni = parsed.get("matched_university", None)

        if found and matched_uni in universities_data:
            matched_info = universities_data[matched_uni]
            result["formula"] = matched_info.get("formula", {})
            result["formula_display"] = matched_info.get("formula_display", "")
            result["found"] = True
            result["matched_university"] = matched_uni
        else:
            # Not found by LLM either
            error_msg = f"University '{university_raw}' could not be matched to any official university list."
            if state is not None:
                state["errors"].append(error_msg)
            print(error_msg)
            
    except Exception as e:
        error_msg = f"Formula picker fallback failed to parse JSON: {str(e)}. Raw output: {response_text}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)

    if state is not None:
        state["formula"] = result["formula"]
        
    return result
