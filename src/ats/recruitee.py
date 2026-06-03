import requests
from src.ats.base import ATSBase

class RecruiteeATS(ATSBase):
    name = "recruitee"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "recruitee" in t

    def fetch_jobs(self, source):
        slug = source.get("slug", "")
        api = source.get("api_url", f"https://{slug}.recruitee.com/api/offers")
        r = requests.get(api, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json().get("offers", [])

    def normalize_job(self, raw, source):
        return {
            "company_name": source["company_name"],
            "title": raw.get("title", ""),
            "location": raw.get("city", raw.get("location", "")),
            "url": raw.get("careers_url", ""),
            "posted_at": (raw.get("published_at", "") or "")[:10],
            "description": raw.get("description", "") or "",
            "source_type": "recruitee"
        }
