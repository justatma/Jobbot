#upload_to_drive_and_update_sheet.py
import os
import sys
import gspread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaFileUpload
from generate_operator_prompt import generate_operator_prompt

# === CONFIGURATION ===
SERVICE_ACCOUNT_FILE = 'continual-grin-443022-v1-6c339e3b7360.json'
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]
OUTPUT_DIR = "pipeline_output"
SHEET_ID = '1cs3ekPl7nDU0KTc-4cn_lxDQFRumnHxrWlENxSalq4Y'
DRIVE_PARENT_FOLDER_NAME = '1) Job Applications'
DRIVE_OPERATOR_JOBS_FOLDER = 'Jobs for Operator'

# === UTILS ===

def sanitize_filename(title):
    safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else "_" for c in title)
    safe = safe.strip().replace(" ", "_")
    return safe

def get_drive_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def find_or_create_folder(service, name, parent_id=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file['id']

def upload_file_to_folder(service, filepath, folder_id):
    file_metadata = {
        'name': os.path.basename(filepath),
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    # Make shareable (only needed for PDFs, but harmless for all)
    service.permissions().create(fileId=file['id'], body={'role': 'reader', 'type': 'anyone'}).execute()
    file_info = service.files().get(fileId=file['id'], fields='webViewLink').execute()
    return file_info['webViewLink']

def set_folder_sharing(service, folder_id):
    service.permissions().create(
        fileId=folder_id,
        body={'type': 'anyone', 'role': 'reader'},
        fields='id'
    ).execute()
    file = service.files().get(fileId=folder_id, fields='webViewLink').execute()
    return file['webViewLink']

# === MAIN LOGIC ===

def main():
    # === Parse command line arguments ===
    if len(sys.argv) < 3:
        print("Usage: python upload_to_drive_and_update_sheet.py <sheet_row_num> <jobname>")
        sys.exit(1)
    SHEET_ROW_NUM = int(sys.argv[1])
    jobname = sys.argv[2]

    # === Google Drive & Sheets Setup ===
    drive_service = get_drive_service()
    sheet_creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(sheet_creds)
    worksheet = gc.open_by_key(SHEET_ID).sheet1

    # Get headers and map column names to their indexes (1-based)
    headers = worksheet.row_values(1)
    col_idx = {name: headers.index(name) + 1 for name in headers}

    # Get job title from the row, and sanitize to base filename
    title = worksheet.cell(SHEET_ROW_NUM, col_idx['Title']).value
    base = sanitize_filename(title)

    # Debug
    print("Job title from sheet:", title)
    print("Sanitized jobname:", base)

    # --- Filepaths for this job ---
    resume_path = os.path.join(OUTPUT_DIR, f"{base}_resume.pdf")
    cover_path = os.path.join(OUTPUT_DIR, f"{base}_coverletter.pdf")
    job_package_path = os.path.join(OUTPUT_DIR, f"{base}_job_package.json")

    answer_bank_path = os.path.join(OUTPUT_DIR, "answer_bank.json")

    # Check if PDF files exist
    for fpath in [resume_path, cover_path, job_package_path, answer_bank_path]:
        if not os.path.exists(fpath):
            print(f"❗ File not found: {fpath}")
            sys.exit(1)

    # === Locate operator jobs folder ===
    parent_results = drive_service.files().list(
        q=f"name='{DRIVE_PARENT_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    parent_folders = parent_results.get('files', [])
    if not parent_folders:
        raise Exception(f"❗ Parent folder '{DRIVE_PARENT_FOLDER_NAME}' not found in My Drive.")
    parent_id = parent_folders[0]['id']

    operator_jobs_id = find_or_create_folder(drive_service, DRIVE_OPERATOR_JOBS_FOLDER, parent_id)

    # === Create/find job folder inside Jobs for Operator ===
    job_folder_name = f"job_{base}"
    job_folder_id = find_or_create_folder(drive_service, job_folder_name, operator_jobs_id)

    # === Set sharing and get folder link ===
    folder_link = set_folder_sharing(drive_service, job_folder_id)
    print("Operator job folder link:", folder_link)

    # === Generate operator prompt file ===
    prompt_path = generate_operator_prompt(folder_link, base)
    print("Generated prompt file at:", prompt_path)

    # === Upload all files ===
    resume_link = upload_file_to_folder(drive_service, resume_path, job_folder_id)
    cover_link = upload_file_to_folder(drive_service, cover_path, job_folder_id)
    upload_file_to_folder(drive_service, job_package_path, job_folder_id)
    upload_file_to_folder(drive_service, answer_bank_path, job_folder_id)
    upload_file_to_folder(drive_service, prompt_path, job_folder_id)

    # === Update Sheet ===
    print("Updating sheet row", SHEET_ROW_NUM)
    try:
        worksheet.update_cell(SHEET_ROW_NUM, col_idx['Status'], "Done")
        worksheet.update_cell(SHEET_ROW_NUM, col_idx['Resume Link'], resume_link)
        worksheet.update_cell(SHEET_ROW_NUM, col_idx['Cover Letter Link'], cover_link)
        worksheet.update_cell(SHEET_ROW_NUM, col_idx['Folder Link'], folder_link)
    except Exception as e:
        print(f"Error updating sheet: {e}")

    print("✅ Upload and sheet update complete for:", jobname)

if __name__ == "__main__":
    main()

