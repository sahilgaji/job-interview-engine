import csv
import hashlib
from src.storage.db import init_db, connect
from src.ats.router import get_ats_by_name
from src.matching.keyword_match import match_job
from src.notify.telegram import send
from src.notify.sheets import append_job, append_run_separator, get_existing_urls
from src.portal_fetcher import fetch_and_parse_rss

def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def make_key(company, title, url):
    raw = f"{company}|{title}|{url}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def save_and_notify(conn, job, seen_urls):
    url = job.get("url", "")
    if not url or url in seen_urls:
        return
    seen_urls.add(url)

    key = make_key(job["company_name"], job["title"], url)
    if conn.execute("SELECT 1 FROM jobs WHERE job_key=?", (key,)).fetchone():
        return

    conn.execute(
        "INSERT INTO jobs (company_name, job_key, title, location, url, posted_at, description, title_score, desc_score, final_score, sheet_row_status, telegram_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (job["company_name"], key, job["title"], job.get("location", ""), url,
         job.get("posted_at", ""), job.get("description", ""), job["title_score"],
         job["desc_score"], job["final_score"], "new", "new")
    )
    conn.commit()

    append_job([
        job["company_name"], job["title"], job.get("location", ""), url,
        job.get("posted_at", ""), job["final_score"], job["title_score"],
        job["desc_score"], "new"
    ])

    if job["final_score"] >= 0.35:
        send(
            f"🚨 <b>New relevant job</b>\n"
            f"<b>{job['company_name']}</b>\n"
            f"{job['title']}\n"
            f"{job.get('location', '')}\n"
            f"{url}"
        )

def process_job(conn, raw_job, seen_urls):
    keep, title_score, desc_score = match_job(
        raw_job["title"],
        raw_job.get("description", ""),
        raw_job.get("location", "")
    )
    if not keep:
        return
    final_score = round(min(1.0, title_score + desc_score), 3)
    if final_score < 0.20:
        return
    raw_job["title_score"] = title_score
    raw_job["desc_score"] = desc_score
    raw_job["final_score"] = final_score
    save_and_notify(conn, raw_job, seen_urls)

def run_ats_targets(conn, seen_urls):
    targets = load_csv("config/company_targets.csv")
    for source in targets:
        ats_name = source.get("ats_type", "").strip().lower()
        api_url = source.get("api_url", "").strip()
        if not ats_name or not api_url:
            print(f"{source['company_name']}: missing ats_type or api_url, skipping")
            continue
        ats = get_ats_by_name(ats_name)
        if not ats:
            print(f"{source['company_name']}: no module for {ats_name}, skipping")
            continue
        try:
            raw_jobs = ats.fetch_jobs(source)
            print(f"{source['company_name']} ({ats_name}): {len(raw_jobs)} jobs fetched")
            matched = 0
            for raw in raw_jobs:
                try:
                    j = ats.normalize_job(raw, source)
                    if not j.get("title") or not j.get("url"):
                        continue
                    keep, title_score, desc_score = match_job(
                        j["title"], j.get("description", ""), j.get("location", "")
                    )
                    if not keep:
                        continue
                    final_score = round(min(1.0, title_score + desc_score), 3)
                    if final_score < 0.20:
                        continue
                    j["title_score"] = title_score
                    j["desc_score"] = desc_score
                    j["final_score"] = final_score
                    save_and_notify(conn, j, seen_urls)
                    matched += 1
                except Exception as e:
                    print(f"  Job processing error: {e}")
            print(f"{source['company_name']}: {matched} new matches saved")
        except Exception as e:
            print(f"{source['company_name']} fetch error: {e}")

def run_rss_portals(conn, seen_urls):
    portals = load_csv("config/portal_sources.csv")
    for p in portals:
        if p.get("source_type") != "rss":
            continue
        jobs = fetch_and_parse_rss(p["url"], p["source_name"])
        matched = 0
        for job in jobs:
            try:
                process_job(conn, job, seen_urls)
                matched += 1
            except Exception as e:
                print(f"  Portal job error: {e}")
        print(f"{p['source_name']}: {matched} new matches saved")

def main():
    init_db()
    print("Fetching existing URLs from sheet for deduplication...")
    seen_urls = get_existing_urls()
    print(f"Found {len(seen_urls)} existing jobs in sheet")
    append_run_separator()

    with connect() as conn:
        print("\n--- Running ATS company targets ---")
        run_ats_targets(conn, seen_urls)
        print("\n--- Running RSS portals ---")
        run_rss_portals(conn, seen_urls)

if __name__ == "__main__":
    main()
