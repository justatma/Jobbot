#main.py
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import subprocess
import difflib
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables if needed
load_dotenv(dotenv_path="/Users/atma/Documents/jobbot/.env")
client = OpenAI()


from keyword_extraction_gpt3_5 import extract_keywords_from_job_description
from write_updated_resume import generate_tailored_resume
from write_cover_letter import generate_cover_letter

OUTPUT_DIR = "pipeline_output"
CREDS_FILE = 'continual-grin-443022-v1-6c339e3b7360.json'
SHEET_NAME = 'PAGE Clipper'
WORKSHEET_NAME = 'Sheet1'

def sanitize_filename(title):
    safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else "_" for c in title)
    safe = safe.strip().replace(" ", "_")
    return safe

def load_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def connect_to_sheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)

def generate_diff(original_text, new_text):
    original_lines = original_text.splitlines()
    new_lines = new_text.splitlines()
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile='Original',
        tofile='Tailored',
        lineterm=''
    )
    return '\n'.join(diff)

def summarize_resume_changes(original_resume, tailored_resume):
    prompt = f"""
You are a world-class resume editor. Compare the following two resumes and summarize the key changes made in the tailored version. 
Highlight additions, removals, major rewrites, and any shifts in tone or emphasis.

ORIGINAL RESUME:
{original_resume}

TAILORED RESUME:
{tailored_resume}

SUMMARY OF CHANGES:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert resume analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def process_jobs():
    sheet = connect_to_sheet()
    data = sheet.get_all_records()
    for i, row in enumerate(data):
        status = row.get("Status", "").lower()
        if status in ("done", "skip", "reviewed"):
            continue

        title = row.get("Title", "")
        jd = row.get("JD", "")
        if not title or not jd:
            print(f"[!] Row {i+2} missing Title or JD. Skipping.")
            continue

        jobname = sanitize_filename(title)

        # 1. Save job description as .txt
        jd_path = os.path.join(OUTPUT_DIR, f"{jobname}_job_desc.txt")
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(jd)
        print(f"[→] Saved JD to: {jd_path}")

        # 2. Keyword Extraction
        extract_keywords_from_job_description(jd_path)

        # 3. Generate tailored resume
        analysis_path = os.path.join(OUTPUT_DIR, f"{jobname}_keywords.json")
        master_resume_path = "Atma_Resume_Master.txt"

        # Confirm files exist before continuing
        if not os.path.exists(analysis_path):
            print(f"[!] Missing keyword analysis file: {analysis_path}. Skipping this job.")
            continue
        if not os.path.exists(master_resume_path):
            print(f"[!] Missing master resume: {master_resume_path}. Exiting.")
            return

        analysis_json = load_text(analysis_path)
        master_resume = load_text(master_resume_path)
        resume_md = generate_tailored_resume(analysis_json, master_resume)

        resume_txt_path = os.path.join(OUTPUT_DIR, f"{jobname}_resume.txt")
        with open(resume_txt_path, "w", encoding="utf-8") as f:
            f.write(resume_md)
        print(f"[✓] Resume saved to: {resume_txt_path}")

        # Generate and save diff
        diff_text = generate_diff(master_resume, resume_md)
        diff_path = os.path.join(OUTPUT_DIR, f"{jobname}_resume_diff.txt")
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write(diff_text)
        print(f"[✓] Resume diff saved to: {diff_path}")

        # Generate and save AI summary of changes
        summary = summarize_resume_changes(master_resume, resume_md)
        summary_path = os.path.join(OUTPUT_DIR, f"{jobname}_resume_change_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"[✓] Resume change summary saved to: {summary_path}")


        # 4. Generate cover letter
        cover_md = generate_cover_letter(analysis_json, resume_snippets=resume_md)
        cover_txt_path = os.path.join(OUTPUT_DIR, f"{jobname}_coverletter.txt")
        with open(cover_txt_path, "w", encoding="utf-8") as f:
            f.write(cover_md)
        print(f"[✓] Cover letter saved to: {cover_txt_path}")

        # 5. Generate PDFs
        subprocess.run(['python', 'generate_pdf_resume.py', jobname])
        subprocess.run(['python', 'generate_pdf_cover.py', jobname])


        import json

        # --- inside the job processing loop, after all other files are generated ---

        # Paths to generated files
        resume_pdf = os.path.join(OUTPUT_DIR, f"{jobname}_resume.pdf")
        cover_pdf = os.path.join(OUTPUT_DIR, f"{jobname}_coverletter.pdf")
        answer_bank_file = os.path.join(OUTPUT_DIR, "answer_bank.json")  # assuming you already have this

        job_package = {
            "job_id": jobname,
            "company": row.get("Title", "").split(" - ")[-1] if " - " in row.get("Title", "") else row.get("Title", ""),
            "title": row.get("Title", ""),
            "application_url": row.get("URL", ""),
            "resume_file": os.path.basename(resume_pdf),
            "cover_file": os.path.basename(cover_pdf),
            "answer_bank_file": os.path.basename(answer_bank_file)
        }

        job_package_path = os.path.join(OUTPUT_DIR, f"{jobname}_job_package.json")


        with open(job_package_path, "w", encoding="utf-8") as f:
            json.dump(job_package, f, indent=2)
        print(f"[✓] job_package.json saved to: {job_package_path}")
 

        print(f"[→] Uploading files and updating sheet for row {i+2} / job '{jobname}'")

        # 6. Upload PDFs + update Sheet
        subprocess.run(['python', 'upload_to_drive_and_update_sheet.py', str(i + 2), jobname])

if __name__ == "__main__":
    process_jobs()
