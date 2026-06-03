import requests
from datetime import datetime, timezone
from src.ats.base import ATSBase

class LeverATS(ATSBase):
    name = "lever"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "lever.co" in t or "jobs.lever.co" in t

    def fetch_jobs(self, source):
        slug = source.get("slug", "")
        api = source.get("api_url", f"https://api.lever.co/v0/postings/{slug}?mode=json")
        r = requests.get(api, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json()

    def normalize_job(self, raw, source):
        posted_at = ""
        ts = raw.get("createdAt")
        if ts:
            posted_at = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        cats = raw.get("categories", {})
        return {
            "company_name": source["company_name"],
            "title": raw.get("text", ""),
            "location": cats.get("location", ""),
            "url": raw.get("hostedUrl", ""),
            "posted_at": posted_at,
            "description": raw.get("descriptionPlain", "") or raw.get("description", ""),
            "source_type": "lever"
        }
