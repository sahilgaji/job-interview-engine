import requests

def fetch_html(url, timeout=20):
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text, r.url

ATS_URL_HINTS = {
    "greenhouse":  ["greenhouse", "boards.greenhouse.io", "job-boards.eu.greenhouse.io"],
    "personio":    ["personio", "jobs.personio.de"],
    "lever":       ["lever.co", "jobs.lever.co"],
    "teamtailor":  ["teamtailor", "api.teamtailor.com"],
    "ashby":       ["ashby", "jobs.ashbyhq.com", "ashbyhq.com"],
    "recruitee":   ["recruitee"],
    "workable":    ["workable", "apply.workable.com"],
    "softgarden":  ["softgarden", "jobdb.softgarden.de"],
    "join":        ["join.com"],
}

def detect_ats_from_text(url, html):
    text = f"{url} {html}".lower()
    for ats_name, hints in ATS_URL_HINTS.items():
        if any(h in text for h in hints):
            return ats_name
    return None

def discover(source):
    explicit = source.get("ats_type", "").strip().lower()
    if explicit:
        return explicit
    try:
        html, final_url = fetch_html(source.get("career_url", ""))
        return detect_ats_from_text(final_url, html)
    except Exception as e:
        print(f"Discovery failed for {source.get('company_name', '?')}: {e}")
        return None
