import requests
import xml.etree.ElementTree as ET
from src.ats.base import ATSBase

class PersonioATS(ATSBase):
    name = "personio"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "personio" in t or "jobs.personio.de" in t

    def fetch_jobs(self, source):
        feed = source.get("api_url", "").strip()
        if not feed:
            raise Exception("No api_url provided for Personio")
        # Safety check — never hit personio.com directly
        if "jobs.personio.de" not in feed and "personio.de/xml" not in feed:
            raise Exception(f"Invalid Personio feed URL: {feed}")
        r = requests.get(feed, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        return root.findall(".//position") or root.findall(".//job")

    def normalize_job(self, raw, source):
        def txt(tag):
            e = raw.find(tag)
            return (e.text or "").strip() if e is not None else ""
        return {
            "company_name": source["company_name"],
            "title": txt("name"),
            "location": txt("office"),
            "url": txt("url"),
            "posted_at": txt("createdAt") or txt("date"),
            "description": txt("jobDescriptions/jobDescription/value") or txt("description"),
            "source_type": "personio"
        }
