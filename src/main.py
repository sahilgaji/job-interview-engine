import csv
import hashlib
from src.storage.db import init_db, connect
from src.monitor.fetcher import fetch
from src.monitor.jsonld_reader import extract_jobpostings
from src.matching.keyword_match import match_job
from src.notify.telegram import send
from src.notify.sheets import append_job_row

def load_companies():
    with open("config/companies_seed.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def make_key(company, title, url, posted_at=""):
    raw = f"{company}|{title}|{url}|{posted_at}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def append_to_sheet(job, score, title_score, desc_score):
    row = [
        job["company_name"],
        job["title"],
        job["location"],
        job["url"],
        job.get("posted_at", ""),
        score,
        title_score,
        desc_score,
        "new"
    ]
    append_job_row(row)

def main():
    init_db()
    companies = load_companies()

    with connect() as conn:
        for c in companies:
            try:
                html, final_url = fetch(c["career_url"])
                jobs = extract_jobpostings(html)

                for j in jobs:
                    title = j.get("title", "")
                    desc = j.get("description", "")
                    url = j.get("url", final_url)
                    posted_at = j.get("datePosted", "")
                    location = ""

                    if isinstance(j.get("jobLocation"), dict):
                        location = j["jobLocation"].get("address", {}).get("addressLocality", "")

                    keep, title_score, desc_score = match_job(title, desc)
                    if not keep:
                        continue

                    final_score = round(min(1.0, title_score + desc_score), 3)
                    if final_score < 0.20:
                        continue

                    job_key = make_key(c["company_name"], title, url, posted_at)
                    exists = conn.execute("SELECT 1 FROM jobs WHERE job_key=?", (job_key,)).fetchone()
                    if exists:
                        continue

                    conn.execute(
                        "INSERT INTO jobs (company_name, job_key, title, location, url, posted_at, description, title_score, desc_score, final_score, sheet_row_status, telegram_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            c["company_name"], job_key, title, location, url, posted_at, desc,
                            title_score, desc_score, final_score, "new", "new"
                        )
                    )
                    conn.commit()

                    append_to_sheet(
                        {
                            "company_name": c["company_name"],
                            "title": title,
                            "location": location,
                            "url": url,
                            "posted_at": posted_at
                        },
                        final_score,
                        title_score,
                        desc_score
                    )

                    if final_score >= 0.35:
                        send(
                            f"🚨 <b>New relevant job</b>\n"
                            f"<b>{c['company_name']}</b>\n"
                            f"{title}\n"
                            f"{location}\n"
                            f"{url}"
                        )

            except Exception:
                continue

if __name__ == "__main__":
    main()
