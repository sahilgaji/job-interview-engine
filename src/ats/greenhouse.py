import re
import requests
from src.ats.base import ATSBase

SLUG_PATTERNS = [
    r'job-boards\.eu\.greenhouse\.io/([a-z0-9_-]+)',
    r'job-boards\.greenhouse\.io/([a-z0-9_-]+)',
    r'boards-api\.greenhouse\.io/v1/boards/([a-z0-9_-]+)',
    r'boards\.greenhouse\.io/([a-z0-9_-]+)',
    r'greenhouse\.io.*?[?&]for=([a-z0-9_-]+)',
    r'"boardToken"\s*:\s*"([a-z0-9_-]+)"',
]

SKIP_SLUGS = {"embed", "jobs", "job_board", "job_app", "internal", "js", "v1"}

def extract_slug(html):
    for pattern in SLUG_PATTERNS:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            slug = match.group(1).lower().strip()
            if slug not in SKIP_SLUGS and len(slug) > 2:
                return slug
    return None

class GreenhouseATS(ATSBase):
    name = "greenhouse"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "greenhouse" in t

    def _try_fetch(self, url):
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
        return jobs

    def fetch_jobs(self, source):
        api_url = source.get("api_url", "").strip()

        # If explicit api_url provided, use it directly
        if api_url:
            return self._try_fetch(api_url)

        # Otherwise try to auto-discover slug from career page
        career_url = source.get("career_url", "").strip()
        if not career_url:
            raise Exception("No api_url or career_url provided")

        try:
            r = requests.get(career_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            slug = extract_slug(r.text)
            if slug:
                print(f"  Auto-discovered slug: {slug}")
                # Try EU endpoint first, then US
                for url in [
                    f"https://job-boards.eu.greenhouse.io/{slug}/jobs?content=true",
                    f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
                ]:
                    try:
                        jobs = self._try_fetch(url)
                        source["api_url"] = url
                        return jobs
                    except Exception:
                        continue
        except Exception as e:
            print(f"  Auto-discovery failed: {e}")

        raise Exception(f"Could not fetch jobs for {source.get('company_name', '?')}")

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
