import requests
from src.ats.base import ATSBase

class AshbyATS(ATSBase):
    name = "ashby"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "ashby" in t or "jobs.ashbyhq.com" in t or "ashbyhq" in t

    def fetch_jobs(self, source):
        slug = source.get("slug", "")
        api = source.get("api_url", f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        r = requests.get(api, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json().get("jobs", [])

    def normalize_job(self, raw, source):
        return {
            "company_name": source["company_name"],
            "title": raw.get("title", ""),
            "location": raw.get("locationName", raw.get("location", "")),
            "url": raw.get("jobUrl", ""),
            "posted_at": (raw.get("publishedDate", "") or "")[:10],
            "description": raw.get("descriptionSocial", raw.get("description", "")) or "",
            "source_type": "ashby"
        }
