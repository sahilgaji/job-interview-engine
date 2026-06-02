import json
from pathlib import Path
from src.utils.text import normalize

PROFILE = json.loads(Path("config/profile.json").read_text(encoding="utf-8"))

def hits(text, keywords):
    t = normalize(text)
    return sum(1 for kw in keywords if kw in t)

def match_job(title, description=""):
    text = normalize(f"{title} {description[:1200]}")
    if any(neg in text for neg in PROFILE["negative_keywords"]):
        return False, 0.0, 0.0

    title_hits = hits(title, PROFILE["positive_keywords"] + PROFILE["target_titles"])
    desc_hits = hits(description[:1200], [
        "stakeholder", "kpi", "dashboard", "agile", "scrum", "jira",
        "confluence", "power bi", "sql", "excel", "reporting", "requirements",
        "business analysis", "operations", "process", "implementation", "rollout"
    ])

    title_score = min(1.0, title_hits * 0.18)
    desc_score = min(1.0, desc_hits * 0.05)

    keep = (title_score >= 0.18) or (desc_score >= 0.20)
    return keep, round(title_score, 3), round(desc_score, 3)
