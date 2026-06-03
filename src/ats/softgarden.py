import requests
from src.ats.base import ATSBase

class SoftgardenATS(ATSBase):
    name = "softgarden"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "softgarden" in t or "jobdb.softgarden.de" in t

    def fetch_jobs(self, source):
        api = source.get("api_url", "")
        r = requests.get(api, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return data.get("jobs", data.get("results", []))

    def normalize_job(self, raw, source):
        return {
            "company_name": source["company_name"],
            "title": raw.get("title", raw.get("jobName", "")),
            "location": raw.get("location", raw.get("geoZone", "")),
            "url": raw.get("url", raw.get("applyUrl", "")),
            "posted_at": (raw.get("datePosted", raw.get("publishedAt", "")) or "")[:10],
            "description": raw.get("description", "") or "",
            "source_type": "softgarden"
        }
