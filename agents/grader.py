import os
import json
import sys
import argparse

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from llm import LLMService

def load_latest_runs() -> dict:
    """Finds and loads the latest run for each student input from runs/ directory."""
    runs_dir = os.path.join(parent_dir, "runs")
    if not os.path.exists(runs_dir):
        return {}
        
    all_runs = []
    for f in os.listdir(runs_dir):
        if f.startswith("run_") and f.endswith(".json"):
            filepath = os.path.join(runs_dir, f)
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    run_data = json.load(file)
                    all_runs.append(run_data)
            except Exception as e:
                print(f"Failed to load run file {f}: {e}")
                
    # Group by student input and get the latest by timestamp
    latest_by_input = {}
    for r in all_runs:
        inp = r.get("student_input")
        ts = r.get("timestamp", "")
        if not inp:
            continue
        if inp not in latest_by_input or ts > latest_by_input[inp].get("timestamp", ""):
            latest_by_input[inp] = r
            
    return latest_by_input

def run_grader(prompt_version: str = "grader_v1.md"):
    print(f"Running AI Grader with prompt version: {prompt_version} ...")
    
    # Load test students to match IDs
    students_path = os.path.join(parent_dir, "data", "test_students.json")
    with open(students_path, "r", encoding="utf-8") as f:
        test_students = json.load(f)
        
    latest_runs = load_latest_runs()
    
    # Load grader prompt
    prompt_path = os.path.join(parent_dir, "prompts", prompt_version)
    with open(prompt_path, "r", encoding="utf-8") as f:
        grader_prompt = f.read().strip()
        
    # Load or initialize reports/grader_scores.json
    scores_path = os.path.join(parent_dir, "reports", "grader_scores.json")
    if os.path.exists(scores_path):
        try:
            with open(scores_path, "r", encoding="utf-8") as f:
                scores_data = json.load(f)
        except Exception:
            scores_data = {}
    else:
        scores_data = {}
        
    # Iterate over completed students and grade them
    for student in test_students:
        raw_input = student["raw_input"]
        student_id = student["id"]
        
        # Check if we have a run for this student
        run = latest_runs.get(raw_input)
        if not run:
            print(f"No run found for {student_id}, skipping.")
            continue
            
        state = run.get("state", {})
        stage = state.get("stage")
        
        # We only grade successful, complete runs
        if stage != "complete":
            print(f"Student {student_id} is in stage '{stage}' (not complete), skipping grading.")
            continue
            
        # Extract inputs for grader
        student_profile = state.get("student_profile", {})
        merit_score = state.get("merit_score", 0.0)
        eligibility = state.get("eligibility", False)
        advice = state.get("advice", "")
        
        grader_payload = {
            "student_profile": student_profile,
            "merit_score": merit_score,
            "eligibility": eligibility,
            "advice": advice
        }
        
        try:
            response_text = LLMService.ask(
                system_prompt=grader_prompt,
                user_input=json.dumps(grader_payload, indent=2),
                system_prompt_name=f"prompts/{prompt_version}"
            )
            parsed_scores = json.loads(response_text.strip())
            
            # Format and save
            if student_id not in scores_data:
                scores_data[student_id] = {}
                
            scores_data[student_id][prompt_version] = {
                "pipeline_version": state.get("pipeline_version", "v3"),
                "grader_prompt_version": prompt_version,
                "realism_score": int(parsed_scores.get("realism_score", 0)),
                "helpfulness_score": int(parsed_scores.get("helpfulness_score", 0)),
                "reasoning": parsed_scores.get("reasoning", ""),
                "advice_evaluated": advice
            }
            print(f"Graded {student_id} successfully: Realism={parsed_scores.get('realism_score')}, Helpfulness={parsed_scores.get('helpfulness_score')}")
        except Exception as e:
            print(f"Failed to grade {student_id}: {e}")
            
    # Save scores file
    os.makedirs(os.path.dirname(scores_path), exist_ok=True)
    with open(scores_path, "w", encoding="utf-8") as f:
        json.dump(scores_data, f, indent=2)
    print(f"Grader scores updated in {scores_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="grader_v1.md", help="Version of the grader prompt to run")
    args = parser.parse_args()
    run_grader(args.version)
