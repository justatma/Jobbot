#generate_pdf_resume.py

import os
import pdfkit
import markdown2

def convert_markdown_txt_to_pdf(txt_path, pdf_path):
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Strip GPT's Markdown code block if present
        if markdown_content.strip().startswith("```markdown"):
            markdown_content = markdown_content.split("```markdown", 1)[-1].strip()

        # Convert Markdown to HTML
        html_body = markdown2.markdown(markdown_content)

        # Add basic styling for readability
        html = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: Arial, sans-serif; 
                font-size: 11pt;
                line-height: 1.5;
                margin: 1in;
            }}
            h1, h2, h3 {{
                font-weight: bold;
                font-size: 13pt;
                margin-top: 24px;
                margin-bottom: 12px;
            }}
            ul {{
                margin-left: 20px;
                padding-left: 10px;
            }}
            li {{
                margin-bottom: 6px;
            }}
        </style>
        </head>
        <body>{html_body}</body>
        </html>
        """

        # Generate PDF from HTML
        pdfkit.from_string(html, pdf_path)
        print(f"[✓] PDF created: {pdf_path}")

    except Exception as e:
        print(f"[✗] PDF conversion failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_pdfs.py <jobname>")
        sys.exit(1)

    jobname = sys.argv[1]
    txt_path = os.path.join("pipeline_output", f"{jobname}_resume.txt")
    pdf_path = os.path.join("pipeline_output", f"{jobname}_resume.pdf")

    if os.path.exists(txt_path):
        convert_markdown_txt_to_pdf(txt_path, pdf_path)
    else:
        print(f"[!] Resume .txt not found: {txt_path}")

