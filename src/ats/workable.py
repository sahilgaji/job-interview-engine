import requests
from src.ats.base import ATSBase

class WorkableATS(ATSBase):
    name = "workable"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "workable" in t or "apply.workable.com" in t

    def fetch_jobs(self, source):
        slug = source.get("slug", "")
        api = source.get("api_url", f"https://apply.workable.com/api/v3/accounts/{slug}/jobs")
        r = requests.get(api, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json().get("results", [])

    def normalize_job(self, raw, source):
        return {
            "company_name": source["company_name"],
            "title": raw.get("title", ""),
            "location": raw.get("location", {}).get("city", "") if isinstance(raw.get("location"), dict) else "",
            "url": raw.get("url", ""),
            "posted_at": (raw.get("published_on", "") or "")[:10],
            "description": raw.get("description", "") or "",
            "source_type": "workable"
        }
