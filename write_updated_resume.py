# write_updated_resume.py

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env environment variable for API key
load_dotenv(dotenv_path="/Users/atma/Documents/jobbot/.env")
client = OpenAI()

# Tailored resume prompt with hard list of required roles
resume_tailoring_prompt = """
SYSTEM MESSAGE
You are an elite career-branding strategist.

Mission: Turn a senior-level marketing résumé into the #1 ATS match AND the most compelling human-readable story.

Constraints:
• Respect plain, single-column formatting (no tables, no graphics).
• Use these exact section labels: Professional Summary, Career Highlights, Core Competencies, Experience, Education, Books
• Contact block must be at the top. Use `**double asterisks**` to bold only the candidate’s name — not the phone number, email, or links. Bold job titles inside the Experience section as appropriate.
• Mirror the company’s tone and values from the input data.
• Every bullet in the Experience section must include: a keyword, a quantifiable outcome or metric, and clear context.
• Embed both the acronym and the long-form of any tools or platforms (e.g., “CDP (customer-data platform)”) once each.
• Remove or compress any roles older than 15 years only if they are no longer relevant.
• Resume may extend beyond 1,800 words to preserve full experience. Prioritize completeness over brevity.
• Do not include footnotes, endnotes, citations, or commentary. Ignore all hyperlinks.
• Do not include a cover letter or ATS checklist in your response.

INPUT PACKET
<<ANALYSIS_JSON>>
{analysis_json}

<<MASTER_RESUME>>
{master_resume}

<<EXTRA_NOTES>>
{extra_notes}

TASK:
Write a tailored résumé only.

Your response must include the **full résumé** from contact block through **all experience**, including:

- Growth Bastards  
- Realware  
- BlockX  
- Point Pickup  
- Savvly  
- Centric Foundation  
- Michelle's Maccs  
- Money Goat  
- Omega ONE  
- Direct Tech  
- Startup Ecology  

Do not truncate. Do not skip roles. Do not compress or summarize unless explicitly instructed. Each experience must retain bullet-level detail. Resume may extend to 1,800+ words if necessary.

Return the output in plain Markdown format, using appropriate section headers, spacing, and bullet formatting.

DO NOT include:
- Any cover letter
- Any checklist
- Any endnotes
- Any commentary

Before finalizing the résumé, ensure:
- All keywords in *keyword_matrix.hard_keywords* appear ≥ 2×  
- Job title is mirrored at least twice  
- Acronym + long-form pairs are present  
- Contact info is at the top and parsable  
"""

def load_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_tailored_resume(analysis_json, master_resume, extra_notes=""):
    prompt = resume_tailoring_prompt.format(
        analysis_json=analysis_json,
        master_resume=master_resume,
        extra_notes=extra_notes
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a world-class AI resume builder."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python write_updated_resume.py <jobname>")
        sys.exit(1)

    jobname = sys.argv[1]
    output_path = os.path.join("pipeline_output", f"{jobname}_resume.txt")

    analysis_path = os.path.join("pipeline_output", f"{jobname}_keywords.json")
    resume_path = "Atma_Resume_Master.txt"

    if not os.path.exists(analysis_path):
        print(f"❗ Missing keyword analysis: {analysis_path}")
        sys.exit(1)

    if not os.path.exists(resume_path):
        print(f"❗ Missing master resume: {resume_path}")
        sys.exit(1)

    analysis_json = load_text(analysis_path)
    master_resume = load_text(resume_path)

    resume = generate_tailored_resume(analysis_json, master_resume)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(resume)

    print(f"[✓] Tailored resume saved to: {output_path}")
