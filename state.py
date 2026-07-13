def create_initial_state(student_input: str = "") -> dict:
    """
    Creates and returns a new dict representing the system state.
    This avoids mutable sharing issues between run instances.
    """
    return {
        "student_input": student_input,
        "student_profile": {},
        "formula": {},
        "merit_score": 0.0,
        "eligibility": False,
        "advice": "",
        "checked": False,
        "grader_score": {},
        "errors": [],
        "stage": "start",
        "intermediate_outputs": {},
        "checker_verdict": {},
        "rewrite_count": 0,
        "pipeline_version": "v3",
        "university_matched": None,
        "cache_hit": False
    }
