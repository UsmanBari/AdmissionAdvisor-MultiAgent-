import unittest

def calculate_merit(marks: dict, formula: dict, standard_totals: dict) -> dict:
    """
    Calculates the weighted merit score.
    Normalizes marks to percentages using student totals or fallbacks.
    Returns: {"merit_score": float or None, "eligibility": bool, "error": str or None}
    """
    merit_score = 0.0
    for subject, weight in formula.items():
        # Get mark entry
        sub_mark = marks.get(subject)
        if not sub_mark:
            return {
                "merit_score": None,
                "eligibility": False,
                "error": f"missing required mark: {subject}"
            }
        
        obtained = sub_mark.get("obtained")
        if obtained is None:
            return {
                "merit_score": None,
                "eligibility": False,
                "error": f"missing required mark: {subject}"
            }
            
        total = sub_mark.get("total")
        if total is None:
            total = standard_totals.get(subject)
            
        if total is None or total <= 0:
            return {
                "merit_score": None,
                "eligibility": False,
                "error": f"missing required total for subject: {subject}"
            }
            
        # Normalization rule: convert to percentage (0-100) first
        percentage = (obtained / total) * 100
        merit_score += percentage * weight

    # Round merit score for standard precision
    merit_score = round(merit_score, 2)
    
    # Temporary placeholder cutoff of 50.0% for eligibility
    # Comment: This cutoff is a placeholder until official university eligibility data is provided.
    eligibility = merit_score >= 50.0
    
    return {
        "merit_score": merit_score,
        "eligibility": eligibility,
        "error": None
    }


class TestCalculator(unittest.TestCase):
    def test_kemu_calculation(self):
        marks = {
            "matric": {"obtained": 1010, "total": 1100},
            "fsc": {"obtained": 970, "total": 1100},
            "mdcat": {"obtained": 185, "total": 200}
        }
        formula = {"matric": 0.10, "fsc": 0.40, "mdcat": 0.50}
        std_totals = {"matric": 1100, "fsc": 1100, "mdcat": 200}
        
        # Matric % = (1010/1100)*100 = 91.818
        # FSc % = (970/1100)*100 = 88.1818
        # MDCAT % = (185/200)*100 = 92.5
        # Weighted = 9.1818 + 35.2727 + 46.25 = 90.70%
        
        res = calculate_merit(marks, formula, std_totals)
        self.assertIsNone(res["error"])
        self.assertEqual(res["merit_score"], 90.7)
        self.assertTrue(res["eligibility"])

    def test_nust_fallback(self):
        # Missing total, should fall back to std_totals
        marks = {
            "fsc": {"obtained": 940, "total": None},
            "net": {"obtained": 142, "total": 200}
        }
        formula = {"fsc": 0.25, "net": 0.75}
        std_totals = {"fsc": 1100, "net": 100}
        
        # FSc fallback total is 1100
        # NET total is specified as 200
        # FSc % = (940/1100)*100 = 85.4545%
        # NET % = (142/200)*100 = 71.0%
        # Weighted = 0.25 * 85.4545 + 0.75 * 71.0 = 21.3636 + 53.25 = 74.61%
        
        res = calculate_merit(marks, formula, std_totals)
        self.assertIsNone(res["error"])
        self.assertEqual(res["merit_score"], 74.61)

    def test_missing_required_mark(self):
        marks = {
            "matric": {"obtained": 1010, "total": 1100},
            "fsc": {"obtained": 970, "total": 1100}
        }
        formula = {"matric": 0.10, "fsc": 0.40, "mdcat": 0.50}
        res = calculate_merit(marks, formula, {})
        self.assertIsNotNone(res["error"])
        self.assertEqual(res["merit_score"], None)
        self.assertIn("missing required mark: mdcat", res["error"])

if __name__ == "__main__":
    unittest.main()
