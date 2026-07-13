import os
import json
import sys

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from llm import LLMService

def run_advisor(profile: dict, formula: dict, merit_score: float, eligibility: bool, state: dict = None, previous_advice: str = None, checker_feedback: str = None) -> dict:
    """
    Advisor agent: generates advice based on profile, formula, merit score, and eligibility.
    Supports a structured rewrite input if previous_advice and checker_feedback are provided.
    Writes only to state["advice"].
    """
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "advisor_v1.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except Exception as e:
        error_msg = f"Advisor failed to load system prompt: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {}

    # Format the input for the LLM Advisor
    if previous_advice is not None and checker_feedback is not None:
        user_input = {
            "student_profile": profile,
            "merit_score": merit_score,
            "eligibility": eligibility,
            "previous_advice": previous_advice,
            "checker_feedback": checker_feedback
        }
    else:
        user_input = {
            "profile": profile,
            "formula": formula,
            "merit_score_percentage": merit_score,
            "eligibility": eligibility
        }

    try:
        response_text = LLMService.ask(
            system_prompt=system_prompt,
            user_input=json.dumps(user_input, indent=2),
            system_prompt_name="prompts/advisor_v1.md"
        )
    except Exception as e:
        error_msg = f"Advisor LLM Service call failed: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {}

    try:
        parsed_data = json.loads(response_text.strip())
        advice = parsed_data.get("advice", "")
        if state is not None:
            state["advice"] = advice
        return parsed_data
    except Exception as e:
        error_msg = f"Advisor failed to parse LLM JSON output: {str(e)}. Raw Output: {response_text}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {}
