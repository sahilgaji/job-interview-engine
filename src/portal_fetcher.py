import feedparser
import requests
from src.utils.text import normalize

def fetch_and_parse_rss(url, source_name):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        feed = feedparser.parse(r.text)
        jobs = []
        for e in feed.entries:
            # Extract company name from title if format is "Job Title - Company Name"
            raw_title = e.get("title", "")
            company = source_name
            title = raw_title
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                title = parts[0].strip()
                company = parts[1].strip()
            elif " | " in raw_title:
                parts = raw_title.rsplit(" | ", 1)
                title = parts[0].strip()
                company = parts[1].strip()

            # Extract location from tags or summary
            location = ""
            if e.get("tags"):
                location = e["tags"][0].get("term", "")

            # Get description
            summary = e.get("summary", e.get("description", ""))
            desc = normalize(summary)

            jobs.append({
                "company_name": company,
                "title": title,
                "location": location,
                "url": e.get("link", ""),
                "posted_at": e.get("published", e.get("updated", ""))[:10] if e.get("published") else "",
                "description": desc,
                "source_type": "rss_portal"
            })
        print(f"{source_name}: {len(jobs)} RSS entries parsed")
        return jobs
    except Exception as e:
        print(f"{source_name} RSS error: {e}")
        return []
