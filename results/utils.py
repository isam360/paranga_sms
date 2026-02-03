# utils.py

def get_grade_and_remark(score):
    """
    NECTA official grading scale (adjusted):
    A: 75–100 → Excellent
    B: 60–74  → Very Good
    C: 50–59  → Good
    D: 40–49  → Pass
    E: 0–39   → Fail
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "", ""  # empty for invalid scores

    if score >= 75:
        return "A", "Excellent"
    elif score >= 60:
        return "B", "Very Good"
    elif score >= 50:
        return "C", "Good"
    elif score >= 40:
        return "D", "Pass"
    else:
        return "E", "Fail"


def score_to_necta_point(score):
    """
    Convert numeric score to NECTA point (lower is better)
    A=1, B=2, C=3, D=4, E/F=5
    """
    if score >= 75:
        return 1
    elif score >= 60:
        return 2
    elif score >= 50:
        return 3
    elif score >= 40:
        return 4
    else:
        return 5


def get_division_from_total_points(total_points):
    """
    Determine NECTA Division from total grade points (best 7 subjects)
    """
    if 7 <= total_points <= 17:
        return "I", "Excellent"
    elif 18 <= total_points <= 21:
        return "II", "Very Good"
    elif 22 <= total_points <= 25:
        return "III", "Good/Satisfactory"
    elif 26 <= total_points <= 33:
        return "IV", "Pass"
    else:
        return "0", "Fail"
