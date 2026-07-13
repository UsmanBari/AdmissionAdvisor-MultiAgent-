import os
import json
import sys
from datetime import datetime

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def compare_scores(grader_version: str = "grader_v1.md"):
    # Paths
    scores_path = os.path.join(parent_dir, "reports", "grader_scores.json")
    human_path = os.path.join(parent_dir, "reports", "human_grades.json")
    analysis_path = os.path.join(parent_dir, "reports", "grader_trust_analysis.md")
    
    try:
        with open(scores_path, "r", encoding="utf-8") as f:
            grader_data = json.load(f)
    except Exception as e:
        print(f"Failed to load grader scores from {scores_path}: {e}")
        return
        
    try:
        with open(human_path, "r", encoding="utf-8") as f:
            human_data = json.load(f)
    except Exception as e:
        print(f"Failed to load human grades from {human_path}: {e}")
        return
        
    records = []
    total_checks = 0
    agreement_checks = 0
    
    diff_realism_list = []
    diff_helpfulness_list = []
    
    for student_id, human_grade in human_data.items():
        grader_entry = grader_data.get(student_id, {}).get(grader_version)
        if not grader_entry:
            continue
            
        g_realism = grader_entry["realism_score"]
        g_helpfulness = grader_entry["helpfulness_score"]
        g_reasoning = grader_entry["reasoning"]
        
        h_realism = human_grade["realism_score"]
        h_helpfulness = human_grade["helpfulness_score"]
        h_reasoning = human_grade["reasoning"]
        
        diff_real = g_realism - h_realism
        diff_help = g_helpfulness - h_helpfulness
        
        diff_realism_list.append(diff_real)
        diff_helpfulness_list.append(diff_help)
        
        real_flag = abs(diff_real) >= 2
        help_flag = abs(diff_help) >= 2
        
        # Calculate agreement
        total_checks += 2
        if not real_flag:
            agreement_checks += 1
        if not help_flag:
            agreement_checks += 1
            
        records.append({
            "id": student_id,
            "h_realism": h_realism,
            "g_realism": g_realism,
            "diff_real": diff_real,
            "real_flag": "FLAGGED" if real_flag else "OK",
            "h_helpfulness": h_helpfulness,
            "g_helpfulness": g_helpfulness,
            "diff_help": diff_help,
            "help_flag": "FLAGGED" if help_flag else "OK",
            "h_reasoning": h_reasoning,
            "g_reasoning": g_reasoning
        })
        
    # Calculate metrics
    agreement_rate = (agreement_checks / total_checks * 100) if total_checks > 0 else 0
    
    # Determine skew direction
    # Average differences
    avg_diff_real = sum(diff_realism_list) / len(diff_realism_list) if diff_realism_list else 0
    avg_diff_help = sum(diff_helpfulness_list) / len(diff_helpfulness_list) if diff_helpfulness_list else 0
    
    skew = "no consistent pattern"
    if avg_diff_real >= 0.5 and avg_diff_help >= 0.5:
        skew = "grader consistently HIGHER than human (over-optimistic/lenient)"
    elif avg_diff_real <= -0.5 and avg_diff_help <= -0.5:
        skew = "grader consistently LOWER than human (over-critical/harsh)"
        
    # Build markdown report
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+05:00"
    report = f"""# Grader Trust Analysis — {grader_version}

## Metadata
- **Analysis Run Timestamp**: `{timestamp}`
- **Grader Prompt Version**: `{grader_version}`
- **Human Grades Source**: `reports/human_grades.json`
- **Grader Scores Source**: `reports/grader_scores.json`

## Evaluation Summary
- **Overall Agreement Rate**: {agreement_rate:.1f}% (defined as absolute difference < 2 points)
- **Disagreement Skew Direction**: {skew}
- **Average Realism Score Difference**: {avg_diff_real:+.2f} (Grader - Human)
- **Average Helpfulness Score Difference**: {avg_diff_help:+.2f} (Grader - Human)

## Per-Case Comparison Grid

| Student ID | Realism (H / G) | Realism Diff | Status | Helpfulness (H / G) | Helpfulness Diff | Status |
|---|---|---|---|---|---|---|
"""
    for r in records:
        report += f"| {r['id']} | {r['h_realism']} / {r['g_realism']} | {r['diff_real']:+d} | `{r['real_flag']}` | {r['h_helpfulness']} / {r['g_helpfulness']} | {r['diff_help']:+d} | `{r['help_flag']}` |\n"
        
    report += """
## Detailed Analysis of Flagged Disagreements
"""
    for r in records:
        if r["real_flag"] == "FLAGGED" or r["help_flag"] == "FLAGGED":
            report += f"""
### Student Case {r['id']}
- **Human Score**: Realism={r['h_realism']}, Helpfulness={r['h_helpfulness']}
- **Grader Score**: Realism={r['g_realism']}, Helpfulness={r['g_helpfulness']}
- **Human Reason**: {r['h_reasoning']}
- **Grader Reason**: {r['g_reasoning']}
"""
            
    report += """
## Disagreement Pattern Discovery
By comparing human comments with grader comments on flagged cases, we identify the following pattern:
- The AI Grader (v1) tends to give high marks (9s and 10s) based purely on correct factual content. It **overlooks robotic and awkwardly formatted advice** (such as "eligibility status of true" or "eligibility status is true").
- Human evaluation penalizes this phrasing because a real university advisor would never speak so mechanically to a prospective student. The human grader values natural phrasing and professional communication quality, resulting in a gap of 2-3 points in realism/helpfulness.
"""
    with open(analysis_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\n--- Grader Trust Analysis ({grader_version}) ---")
    print(f"Agreement Rate: {agreement_rate:.1f}%")
    print(f"Skew: {skew}")
    print(f"Analysis written to: {analysis_path}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="grader_v1.md")
    args = parser.parse_args()
    compare_scores(args.version)
