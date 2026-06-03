import requests
from src.ats.base import ATSBase

class TeamtailorATS(ATSBase):
    name = "teamtailor"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "teamtailor" in t or "api.teamtailor.com" in t

    def fetch_jobs(self, source):
        api = source.get("api_url", "")
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Api-Version": "20210218"
        }
        r = requests.get(api, timeout=30, headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])

    def normalize_job(self, raw, source):
        attrs = raw.get("attributes", {})
        return {
            "company_name": source["company_name"],
            "title": attrs.get("title", ""),
            "location": "",
            "url": attrs.get("canonical-url", attrs.get("canonical_url", "")),
            "posted_at": (attrs.get("created-at", "") or "")[:10],
            "description": attrs.get("body", "") or "",
            "source_type": "teamtailor"
        }
