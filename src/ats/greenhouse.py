import re
import requests
from src.ats.base import ATSBase

SLUG_PATTERNS = [
    r'boards-api\.greenhouse\.io/v1/boards/([^/"\s]+)',
    r'boards\.greenhouse\.io/([^/"\s?&]+)',
    r'job-boards\.greenhouse\.io/([^/"\s?&]+)',
    r'job-boards\.eu\.greenhouse\.io/([^/"\s?&]+)',
    r'greenhouse\.io/embed/job_board\?for=([^&"\s]+)',
    r'"for"\s*:\s*"([^"]+)"',
    r"boardURI.*?greenhouse\.io.*?/([a-z0-9_-]{3,40})[/\"']",
]

def extract_slug_from_html(html):
    for pattern in SLUG_PATTERNS:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            slug = match.group(1).lower().strip()
            if slug not in ("embed", "jobs", "job_board", "job_app", "internal"):
                return slug
    return None

def build_api_url(slug, eu=False):
    if eu:
        return f"https://job-boards.eu.greenhouse.io/{slug}/jobs?content=true"
    return f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

class GreenhouseATS(ATSBase):
    name = "greenhouse"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "greenhouse" in t or "boards-api.greenhouse.io" in t or "boards.greenhouse.io" in t

    def fetch_jobs(self, source):
        # Use explicit api_url if provided and known good
        api_url = source.get("api_url", "").strip()

        # If no api_url, try to discover slug from career page
        if not api_url:
            career_url = source.get("career_url", "")
            if career_url:
                try:
                    r = requests.get(career_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
                    slug = extract_slug_from_html(r.text)
                    if slug:
                        print(f"  Auto-discovered slug: {slug}")
                        api_url = build_api_url(slug)
                        source["api_url"] = api_url
                except Exception as e:
                    print(f"  Slug discovery failed: {e}")

        if not api_url:
            print(f"  No API URL for {source.get('company_name', '?')}, skipping")
            return []

        # Try the URL, fall back to EU endpoint if 404
        try:
            r = requests.get(api_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 404 and "boards-api" in api_url:
                slug = api_url.split("/boards/")[1].split("/")[0]
                eu_url = build_api_url(slug, eu=True)
                r = requests.get(eu_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.json().get("jobs", [])
        except Exception as e:
            raise Exception(f"Greenhouse fetch failed: {e}")

    def normalize_job(self, raw, source):
        loc = raw.get("location", {})
        location = loc.get("name", "") if isinstance(loc, dict) else str(loc)
        return {
            "company_name": source["company_name"],
            "title": raw.get("title", ""),
            "location": location,
            "url": raw.get("absolute_url", ""),
            "posted_at": (raw.get("updated_at") or raw.get("created_at", ""))[:10],
            "description": raw.get("content", "") or "",
            "source_type": "greenhouse"
        }
