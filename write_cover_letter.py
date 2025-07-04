# write_cover_letter.py   3.0

# write_cover_letter.py

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv(dotenv_path="/Users/atma/Documents/jobbot/.env")
client = OpenAI()

cover_letter_prompt = """
SYSTEM MESSAGE  
You are a world-class career branding strategist and storyteller. Your mission is to write a powerful one-page cover letter for a senior-level marketing role.

Constraints:
• Use a clear, confident, professional voice that reflects warmth, intelligence, and executive-level presence.  
• Structure:  
  - Paragraph 1: Hook — reference company mission, recent success, or product insight.  
  - Paragraph 2: Alignment — why my background fits *key_responsibilities*.  
  - Paragraph 3: Culture fit — echo *culture_values* and tone.  
  - Paragraph 4: Call to action and polite close.  
• Include a greeting ("Dear Hiring Team,"). **Do NOT include any closing, sign-off, or signature** (the system will insert it automatically).
• Length: ~250–300 words max.  
• Mirror the tone and language found in *tone_style* and *culture_phrases*.  
• If provided, draw one or two strong points from the tailored résumé for credibility.  
• Do not repeat the résumé. This is a narrative complement — not a summary.

INPUT PACKET
<<ANALYSIS_JSON>>
{analysis_json}

<<EXTRA_NOTES>>
{extra_notes}

<<OPTIONAL_RESUME_SNIPPETS>>
{resume_snippets}

TASK:
Write a single compelling cover letter tailored to the role described above using the structure and tone guidelines given. Address it “Dear Hiring Team.” Do NOT include a closing or signature 
block—just end the letter body with a polite, forward-looking final paragraph.
"""

def load_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def remove_closing(cover_md):
    # Remove any closing/signature lines (handles multiple types and all lines after first closing)
    closing_triggers = [
        'Best wishes,', 'Sincerely,', 'Kind regards,', 'Warm regards,',
        'Yours truly,', 'Yours sincerely,', 'Regards,'
    ]
    lines = cover_md.strip().split('\n')
    for i, line in enumerate(lines):
        if any(line.strip().lower().startswith(c.lower()) for c in closing_triggers):
            return '\n'.join(lines[:i]).rstrip()
    return cover_md.rstrip()

def generate_cover_letter(analysis_json, extra_notes="", resume_snippets=""):
    prompt = cover_letter_prompt.format(
        analysis_json=analysis_json,
        extra_notes=extra_notes,
        resume_snippets=resume_snippets
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a strategic storytelling expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    # Always remove closing in case the LLM still sneaks one in
    body_only = remove_closing(response.choices[0].message.content.strip())
    return body_only

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python write_cover_letter.py <jobname>")
        sys.exit(1)

    jobname = sys.argv[1]
    OUTPUT_DIR = "pipeline_output"

    keywords_path = os.path.join(OUTPUT_DIR, f"{jobname}_keywords.json")
    resume_snippets_path = os.path.join(OUTPUT_DIR, f"{jobname}_tailored_résumé.txt")
    output_path = os.path.join(OUTPUT_DIR, f"{jobname}_coverletter.txt")

    if not os.path.exists(keywords_path):
        print(f"❗ Keywords file not found: {keywords_path}")
        sys.exit(1)

    analysis_json = load_text(keywords_path)
    resume_snippets = load_text(resume_snippets_path) if os.path.exists(resume_snippets_path) else ""

    result = generate_cover_letter(analysis_json, resume_snippets=resume_snippets)
    cleaned_result = remove_closing(result)  # Double-safety: remove again if needed

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_result)

    print(f"✔ Cover letter saved to: {output_path}")

