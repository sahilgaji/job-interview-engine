import sqlite3
from pathlib import Path

DB_PATH = Path("data/job_engine.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    job_key TEXT UNIQUE,
    title TEXT,
    location TEXT,
    url TEXT,
    posted_at TEXT,
    description TEXT,
    title_score REAL DEFAULT 0,
    desc_score REAL DEFAULT 0,
    final_score REAL DEFAULT 0,
    sheet_row_status TEXT DEFAULT 'new',
    telegram_status TEXT DEFAULT 'new',
    first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()
