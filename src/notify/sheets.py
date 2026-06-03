import os
import gspread
from datetime import datetime, timezone
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = os.getenv("SHEET_NAME", "Jobs")

def client():
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    return gspread.authorize(creds)

def get_existing_urls():
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        return set()
    try:
        gc = client()
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(SHEET_NAME)
        url_col = ws.col_values(4)
        return set(url_col[1:])
    except Exception as e:
        print(f"Could not fetch existing URLs: {e}")
        return set()

def append_run_separator():
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        return
    try:
        gc = client()
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(SHEET_NAME)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ws.append_row(
            ["--- NEW RUN ---", now, "", "", "", "", "", "", ""],
            value_input_option="RAW"
        )
    except Exception as e:
        print(f"Could not append run separator: {e}")

def append_job(row):
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        return
    try:
        gc = client()
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(SHEET_NAME)
        ws.append_row(row, value_input_option="RAW")
    except Exception as e:
        print(f"Could not append job row: {e}")
