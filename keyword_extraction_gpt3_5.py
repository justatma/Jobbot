# keyword_extraction_gpt3_5.py

import os
import json
import tiktoken
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/atma/Documents/jobbot/.env")
client = OpenAI()

# Constants
GPT_MODEL = "gpt-3.5-turbo"
MAX_PROMPT_TOKENS = 8000
OUTPUT_FOLDER = "pipeline_output"
SYSTEM_PROMPT = """
You are a world-class job application assistant. You will receive a full job description and must extract key insights in JSON format. Please identify the role's overview, responsibilities, required and preferred 
skills, company culture, tone, and relevant keyword clusters for resume tailoring.
"""

def count_tokens(text: str, model: str = GPT_MODEL) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def extract_keywords_from_job_description(job_desc_path):
    with open(job_desc_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()

    prompt_raw = f"{SYSTEM_PROMPT}\n\n{jd_text}"
    total_tokens = count_tokens(prompt_raw)

    if total_tokens > MAX_PROMPT_TOKENS:
        print(f"[!] Prompt too long ({total_tokens} tokens). Truncating...")
        allowable = MAX_PROMPT_TOKENS - count_tokens(SYSTEM_PROMPT) - 200
        jd_tokens = tiktoken.encoding_for_model(GPT_MODEL).encode(jd_text)
        jd_text = tiktoken.encoding_for_model(GPT_MODEL).decode(jd_tokens[:allowable])

    print(f"[INFO] Final prompt token count: {count_tokens(f'{SYSTEM_PROMPT}\n\n{jd_text}')}")

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": jd_text.strip()}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content

    # Try to parse clean JSON
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print("[!] Error parsing JSON. Attempting to extract valid JSON...")
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                print("[!!] Fallback failed. Saving raw string.")
                parsed = {"raw_response": content}
        else:
            parsed = {"raw_response": content}


    filename = os.path.basename(job_desc_path).replace("_job_desc.txt", "_keywords.json").replace(".txt", "_keywords.json")

    output_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(parsed, out_f, indent=2)
        print(f"[✓] Saved keyword output to {output_path}")

    return parsed

# Test run — use one of the following:
# extract_keywords_from_job_description("pipeline_output/A24_job_desc.txt")
# extract_keywords_from_job_description("pipeline_output/Job_Desc_Director_of_Growth_Marketing.txt")

