import os
import json
import sys

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from llm import LLMService

def run_checker(merit_score: float, eligibility: bool, advice: str, state: dict = None) -> dict:
    """
    Checker agent: judges whether the generated advice is consistent with the calculated merit score and eligibility.
    Only sees merit_score, eligibility, and advice.
    Returns: {"approved": bool/None, "reason": str}
    """
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "checker_v1.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except Exception as e:
        error_msg = f"Checker failed to load system prompt: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {"approved": None, "reason": "checker failed to load system prompt"}

    # Structured payload ensuring the Checker ONLY sees the three allowed fields
    checker_input = {
        "merit_score": merit_score,
        "eligibility": eligibility,
        "advice": advice
    }

    try:
        response_text = LLMService.ask(
            system_prompt=system_prompt,
            user_input=json.dumps(checker_input, indent=2),
            system_prompt_name="prompts/checker_v1.md"
        )
    except Exception as e:
        error_msg = f"Checker LLM Service call failed: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {"approved": None, "reason": "checker LLM call failed"}

    try:
        parsed_data = json.loads(response_text.strip())
        approved = parsed_data.get("approved")
        reason = parsed_data.get("reason", "")
        
        # Coerce approved to bool if possible
        if not isinstance(approved, bool) and approved is not None:
            if str(approved).lower() == "true":
                approved = True
            elif str(approved).lower() == "false":
                approved = False
            else:
                approved = None
                
        return {"approved": approved, "reason": reason}
    except Exception as e:
        error_msg = f"Checker failed to parse LLM JSON output: {str(e)}. Raw Output: {response_text}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {"approved": None, "reason": "checker failed to return valid output"}
