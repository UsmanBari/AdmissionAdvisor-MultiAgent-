import os
import json
import sys

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from llm import LLMService

def run_reader(student_input: str, state: dict = None) -> dict:
    """
    Reader agent: extracts structured marks (obtained and total) and target university name.
    Writes only to state["student_profile"]. Never touches formula, score, or advice.
    """
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "reader_v1.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except Exception as e:
        error_msg = f"Reader failed to load system prompt: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {}

    try:
        response_text = LLMService.ask(
            system_prompt=system_prompt,
            user_input=student_input,
            system_prompt_name="prompts/reader_v1.md"
        )
    except Exception as e:
        error_msg = f"Reader LLM Service call failed: {str(e)}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {}

    try:
        parsed_data = json.loads(response_text.strip())
        if state is not None:
            state["student_profile"] = parsed_data
        return parsed_data
    except Exception as e:
        error_msg = f"Reader failed to parse LLM JSON output: {str(e)}. Raw Output: {response_text}"
        if state is not None:
            state["errors"].append(error_msg)
        print(error_msg)
        return {}
