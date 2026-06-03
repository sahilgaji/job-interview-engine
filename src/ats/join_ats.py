import requests
from src.ats.base import ATSBase

class JoinATS(ATSBase):
    name = "join"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "join.com" in t

    def fetch_jobs(self, source):
        slug = source.get("slug", "")
        api = source.get("api_url", f"https://api.join.com/v1/companies/{slug}/jobs")
        r = requests.get(api, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("jobs", [])

    def normalize_job(self, raw, source):
        return {
            "company_name": source["company_name"],
            "title": raw.get("title", raw.get("name", "")),
            "location": raw.get("location", {}).get("city", "") if isinstance(raw.get("location"), dict) else "",
            "url": raw.get("url", raw.get("applyUrl", "")),
            "posted_at": (raw.get("publishedAt", raw.get("createdAt", "")) or "")[:10],
            "description": raw.get("description", "") or "",
            "source_type": "join"
        }
