import json
from bs4 import BeautifulSoup

def extract_jobpostings(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.get_text(strip=True))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    out.append(item)
        except Exception:
            pass
    return out
