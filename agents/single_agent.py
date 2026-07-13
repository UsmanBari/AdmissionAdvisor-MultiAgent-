import os
import json
from datetime import datetime
import sys

# Ensure parent directory is in path so we can import config, llm, state
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from llm import LLMService
from state import create_initial_state

def get_next_run_filepath() -> str:
    """
    Finds the next auto-incrementing file path in runs/ folder.
    e.g., runs/run_001.json, runs/run_002.json, etc.
    """
    os.makedirs("runs", exist_ok=True)
    counter = 1
    while True:
        filename = f"run_{counter:03d}.json"
        filepath = os.path.join("runs", filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1

def run_single_agent(student_input: str) -> dict:
    """
    Runs the single agent flow for a given student input.
    """
    state = create_initial_state(student_input=student_input)
    
    # Load prompt from prompts/single_agent_v1.md
    prompt_path = os.path.join("prompts", "single_agent_v1.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except Exception as e:
        error_msg = f"Failed to load system prompt from {prompt_path}: {str(e)}"
        state["errors"].append(error_msg)
        print(error_msg)
        return state

    # Call LLM
    try:
        response_text = LLMService.ask(
            system_prompt=system_prompt,
            user_input=student_input,
            system_prompt_name="prompts/single_agent_v1.md"
        )
    except Exception as e:
        error_msg = f"LLM Service call failed: {str(e)}"
        state["errors"].append(error_msg)
        print(error_msg)
        return state

    # Parse JSON (be strict - do not patch it if invalid)
    try:
        parsed_data = json.loads(response_text.strip())
        state["merit_score"] = parsed_data.get("merit_score", 0.0)
        state["eligibility"] = parsed_data.get("eligibility", False)
        state["advice"] = parsed_data.get("advice", "")
    except Exception as e:
        error_msg = f"Failed to parse LLM JSON output: {str(e)}. Raw Output: {response_text}"
        state["errors"].append(error_msg)
        print(error_msg)

    # Save run info
    run_filepath = get_next_run_filepath()
    run_record = {
        "student_input": student_input,
        "state": state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "prompt_version": "single_agent_v1.md"
    }
    
    try:
        with open(run_filepath, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2)
        print(f"Run saved successfully to {run_filepath}")
    except Exception as e:
        print(f"Failed to write run record to {run_filepath}: {str(e)}")
        
    return state
