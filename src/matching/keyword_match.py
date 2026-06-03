import json
from pathlib import Path
from src.utils.text import normalize

PROFILE = json.loads(Path("config/profile.json").read_text(encoding="utf-8"))

STRONG_TITLE_SIGNALS = [
    "junior", "associate", "coordinator", "analyst", "specialist",
    "assistant", "intern", "working student", "graduate", "trainee",
    "pmo", "business operations", "project management", "digital transformation",
    "process improvement", "implementation", "reporting", "operations",
    "projektkoordinator", "projektassistent", "projektmanager",
    "prozessanalyst", "prozesskoordinator", "prozessmanager",
    "digitalisierung", "transformation", "koordinator", "koordinatorin",
    "referent", "referentin", "werkstudent", "werkstudentin",
    "spezialist", "spezialistin", "berater", "beraterin",
    "projektleiter", "projektleiterin", "analyst", "analystin"
]

BLOCKED_SENIORITY = [
    "senior", "lead", "principal", "head of", "director", "vp",
    "vice president", "ceo", "cto", "cfo", "coo", "manager",
    "leiterin", "leiter", "abteilungsleiter", "teamleiter",
    "teamleiterin", "gruppenleiter", "gruppenleiterin"
]


def _hits(text, keywords):
    t = normalize(text)
    return sum(1 for kw in keywords if kw.lower() in t)


def is_relevant_location(location):
    if not location:
        return True
    loc = normalize(location)
    if "remote" in loc:
        return True
    return any(normalize(gl) in loc for gl in PROFILE["locations"])


def match_job(title, description="", location=""):
    text = normalize(f"{title} {description[:1500]}")
    title_lower = normalize(title)

    # Hard block: wrong seniority in title
    if any(s in title_lower for s in BLOCKED_SENIORITY):
        return False, 0.0, 0.0

    # Hard block: negative keywords anywhere in text
    if any(neg.lower() in text for neg in PROFILE["negative_keywords"]):
        return False, 0.0, 0.0

    # Hard block: location not relevant
    if location and not is_relevant_location(location):
        return False, 0.0, 0.0

    # Title must have a signal word OR match a target title directly
    title_has_signal = any(s in title_lower for s in STRONG_TITLE_SIGNALS)
    title_matches_target = any(normalize(t) in title_lower for t in PROFILE["target_titles"])
    if not title_has_signal and not title_matches_target:
        return False, 0.0, 0.0

    title_hits = _hits(title, PROFILE["positive_keywords"] + PROFILE["target_titles"])
    desc_hits = _hits(description[:1500], [
        "stakeholder", "kpi", "dashboard", "agile", "scrum", "jira", "confluence",
        "power bi", "sql", "excel", "reporting", "requirements", "business analysis",
        "operations", "process", "implementation", "rollout", "prozess",
        "projektmanagement", "digitalisierung", "veränderungsmanagement",
        "anforderungen", "berichterstattung"
    ])

    title_score = min(1.0, title_hits * 0.20)
    desc_score = min(1.0, desc_hits * 0.05)
    keep = (title_score >= 0.20) or (desc_score >= 0.20)
    return keep, round(title_score, 3), round(desc_score, 3)
