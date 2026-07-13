import os
import json
import re
from datetime import datetime

# Define root directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_summary():
    print("Generating dashboard summary data...")
    
    # 1. Scan run files in runs/
    runs_dir = os.path.join(root_dir, "runs")
    total_runs = 0
    cache_hits = 0
    rewrites = 0
    stage_breakdown = {
        "complete": 0,
        "failed_at_reader": 0,
        "failed_at_formula_picker": 0,
        "failed_at_calculator": 0,
        "failed_at_advisor": 0,
        "failed_at_checker": 0
    }
    
    if os.path.exists(runs_dir):
        for f in os.listdir(runs_dir):
            if f.startswith("run_") and f.endswith(".json"):
                filepath = os.path.join(runs_dir, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        run_data = json.load(file)
                        state = run_data.get("state", {})
                        total_runs += 1
                        
                        # Cache hit tracking
                        if state.get("cache_hit") is True:
                            cache_hits += 1
                            
                        # Rewrite tracking
                        # Checked if advisor_attempt_2 duration_ms exists or rewrite_count > 0
                        if state.get("rewrite_count", 0) > 0 or "advisor_attempt_2" in state.get("intermediate_outputs", {}):
                            rewrites += 1
                            
                        # Stage breakdown tracking
                        stage = state.get("stage", "unknown")
                        if stage in stage_breakdown:
                            stage_breakdown[stage] += 1
                        else:
                            stage_breakdown[stage] = stage_breakdown.get(stage, 0) + 1
                except Exception as e:
                    print(f"Skipping run file {f} due to error: {e}")
                    
    cache_hit_rate = (cache_hits / total_runs * 100) if total_runs > 0 else 0.0
    rewrite_rate = (rewrites / stage_breakdown.get("complete", 1) * 100) if stage_breakdown.get("complete", 0) > 0 else 0.0

    # 2. Parse test results report (last segment)
    test_report_path = os.path.join(root_dir, "reports", "test_results_day7.md")
    test_metrics = {
        "students_tested": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "accuracy": 0.0
    }
    
    if os.path.exists(test_report_path):
        try:
            with open(test_report_path, "r", encoding="utf-8") as file:
                content = file.read()
                
            # Grab the last segment of the report (in case of historical follow-ups)
            segments = content.split("---")
            target_segment = segments[-1] if segments else content
            
            # Extract metrics using regex
            tested_match = re.search(r"-\s+\*\*Students Tested\*\*:\s*(\d+)", target_segment)
            passed_match = re.search(r"-\s+\*\*Passed \(all criteria\)\*\*:\s*(\d+)", target_segment)
            failed_match = re.search(r"-\s+\*\*Failed \(at least one criterion\)\*\*:\s*(\d+)", target_segment)
            errors_match = re.search(r"-\s+\*\*Pipeline Errors\*\*\:\s*(\d+)", target_segment)
            accuracy_match = re.search(r"-\s+\*\*Accuracy\*\*:\s*([\d\.]+)%", target_segment)
            
            if tested_match: test_metrics["students_tested"] = int(tested_match.group(1))
            if passed_match: test_metrics["passed"] = int(passed_match.group(1))
            if failed_match: test_metrics["failed"] = int(failed_match.group(1))
            if errors_match: test_metrics["errors"] = int(errors_match.group(1))
            if accuracy_match: test_metrics["accuracy"] = float(accuracy_match.group(1))
        except Exception as e:
            print(f"Failed to parse test report metrics: {e}")

    # Compile data
    dashboard_data = {
        "total_runs": total_runs,
        "cache_hits": cache_hits,
        "cache_hit_rate": round(cache_hit_rate, 1),
        "rewrites": rewrites,
        "rewrite_rate": round(rewrite_rate, 1),
        "runs_by_stage": stage_breakdown,
        "test_accuracy": test_metrics,
        "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+05:00"
    }

    # Save output to data/dashboard_summary.json and data/dashboard_summary.js
    data_dir = os.path.join(root_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    json_path = os.path.join(data_dir, "dashboard_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)
        
    js_path = os.path.join(data_dir, "dashboard_summary.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DASHBOARD_DATA = {json.dumps(dashboard_data, indent=2)};\n")
        
    print(f"Summary JSON generated at: {json_path}")
    print(f"Summary JS generated at: {js_path}")

if __name__ == "__main__":
    generate_summary()
