import csv
import hashlib
from src.storage.db import init_db, connect
from src.ats.router import get_ats_by_name
from src.matching.keyword_match import match_job
from src.notify.telegram import send
from src.notify.sheets import append_job_row

def load_targets():
    with open("config/company_targets.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def make_key(company, title, url):
    raw = f"{company}|{title}|{url}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def save_and_notify(conn, job):
    key = make_key(job["company_name"], job["title"], job["url"])
    if conn.execute("SELECT 1 FROM jobs WHERE job_key=?", (key,)).fetchone():
        return
    conn.execute(
        "INSERT INTO jobs (company_name, job_key, title, location, url, posted_at, description, title_score, desc_score, final_score, sheet_row_status, telegram_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (job["company_name"], key, job["title"], job["location"], job["url"],
         job["posted_at"], job["description"], job["title_score"], job["desc_score"],
         job["final_score"], "new", "new")
    )
    conn.commit()
    append_job_row([
        job["company_name"], job["title"], job["location"], job["url"],
        job["posted_at"], job["final_score"], job["title_score"], job["desc_score"], "new"
    ])
    if job["final_score"] >= 0.35:
        send(
            f"🚨 <b>New relevant job</b>\n"
            f"<b>{job['company_name']}</b>\n"
            f"{job['title']}\n"
            f"{job['location']}\n"
            f"{job['url']}"
        )

def process_source(conn, source):
    ats_name = source.get("ats_type", "").strip().lower()
    api_url = source.get("api_url", "").strip()

    if not ats_name or not api_url:
        print(f"{source['company_name']}: missing ats_type or api_url, skipping")
        return

    ats = get_ats_by_name(ats_name)
    if not ats:
        print(f"{source['company_name']}: no module for {ats_name}, skipping")
        return

    try:
        raw_jobs = ats.fetch_jobs(source)
        print(f"{source['company_name']} ({ats_name}): {len(raw_jobs)} jobs fetched")
        matched = 0
        for raw in raw_jobs:
            try:
                j = ats.normalize_job(raw, source)
                if not j.get("title") or not j.get("url"):
                    continue
                keep, title_score, desc_score = match_job(j["title"], j.get("description", ""))
                if not keep:
                    continue
                final_score = round(min(1.0, title_score + desc_score), 3)
                if final_score < 0.20:
                    continue
                j["title_score"] = title_score
                j["desc_score"] = desc_score
                j["final_score"] = final_score
                save_and_notify(conn, j)
                matched += 1
            except Exception as e:
                print(f"  Job processing error: {e}")
        print(f"{source['company_name']}: {matched} matches saved")
    except Exception as e:
        print(f"{source['company_name']} fetch error: {e}")

def main():
    init_db()
    targets = load_targets()
    with connect() as conn:
        for source in targets:
            process_source(conn, source)

if __name__ == "__main__":
    main()
