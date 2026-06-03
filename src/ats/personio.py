import re
import requests
import xml.etree.ElementTree as ET
from src.ats.base import ATSBase


def find_personio_slug(career_url):
    try:
        r = requests.get(career_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        match = re.search(r'([a-z0-9-]+)\.jobs\.personio\.(?:de|com)', r.text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    except Exception:
        pass
    return None


class PersonioATS(ATSBase):
    name = "personio"
    public = True

    def detect(self, url, html):
        t = f"{url} {html}".lower()
        return "personio" in t or "jobs.personio.de" in t

    def fetch_jobs(self, source):
        feed = source.get("api_url", "").strip()

        # Validate the feed URL — must be a company-specific Personio XML feed
        if not feed or "jobs.personio.de" not in feed:
            # Try to auto-discover slug from career page
            slug = find_personio_slug(source.get("career_url", ""))
            if slug:
                feed = f"https://{slug}.jobs.personio.de/xml"
                print(f"  Auto-discovered Personio slug: {slug}")
            else:
                raise Exception(f"No valid Personio feed URL for {source.get('company_name', '?')}")

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
