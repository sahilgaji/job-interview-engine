import requests
from src.ats.base import ATSBase

class GreenhouseATS(ATSBase):
    name = "greenhouse"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "greenhouse" in t or "boards-api.greenhouse.io" in t or "boards.greenhouse.io" in t

    def fetch_jobs(self, source):
        api_url = source.get("api_url", "")
        if not api_url:
            slug = source.get("slug", "")
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        r = requests.get(api_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json().get("jobs", [])

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
