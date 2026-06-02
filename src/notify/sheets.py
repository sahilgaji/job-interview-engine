import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = os.getenv("SHEET_NAME", "Jobs")

def get_client():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)

def append_job_row(row):
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        return
    gc = get_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(SHEET_NAME)
    ws.append_row(row, value_input_option="RAW")
