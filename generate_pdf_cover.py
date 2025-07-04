import os
import pdfkit
import markdown2
import re

def convert_markdown_txt_to_pdf(txt_path, pdf_path):
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert Markdown to HTML
        html_body = markdown2.markdown(markdown_content)

        # Remove all <strong>, <b>, <em>, <i> tags
        html_body = re.sub(r'</?(strong|b|em|i)>', '', html_body, flags=re.IGNORECASE)
        html_body = re.sub(r'style="[^"]*font-weight:\s*bold;?[^"]*"', '', html_body, flags=re.IGNORECASE)
        # Replace <p> tags with forced inline style
        html_body = re.sub(
            r'<p(\s*?)>',
            r'<p style="font-weight:normal !important; font-family:Arial,Helvetica,sans-serif !important;">',
            html_body
        )

        html = f"""<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700,800&display=swap" rel="stylesheet">

<style>
@page {{
    margin: 1.3in 1.3in 1.3in 1.3in;
}}
body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 12.5pt;
    line-height: 1.7;
    color: #222;
}}
.letterhead {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: end;
    margin-bottom: 0.15em;
}}
.letterhead-content {{
    text-align: right;
    grid-column: 2;
}}
.letterhead .name {{
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-bottom: 0;
}}
.letterhead .hr {{
    border: 0;
    border-top: 2px solid #bbb;
    margin: 0.16em 0 0.11em 0;
    width: 100%;
}}
.letterhead .location {{
    font-size: 12pt;
    font-weight: 400;
    color: #888;
    margin-top: 0;
    text-align: right;
}}
.date {{
    text-align: left;
    font-size: 12.2pt;
    font-weight: bold;
    margin-bottom: 1.12em;
    margin-top: 0.6em;
}}
.letter-body, .letter-body * {{
    font-weight: normal !important;
    text-align: left;
    font-family: Arial, Helvetica, sans-serif !important;
}}
.closing {{
    margin-top: 1.9em;
    font-weight: normal;
}}
.signature-block {{
    margin-top: 1.3em;
    font-size: 12pt;
    line-height: 1.5;
    text-align: left;
    font-weight: bold;
}}
.sig-name {{
    font-weight: bold;
    font-style: italic;
    font-size: 13pt;
    display: block;
    margin-bottom: 0.12em;
}}
.sig-title,
.sig-email,
.sig-phone {{
    font-weight: bold;
    font-style: normal;
    display: block;
    margin-bottom: 0.04em;
}}
</style>
</head>
<body>
<div class="letterhead">
    <div></div>
    <div class="letterhead-content">
        <div class="name">Atma...</div>
        <div class="hr"></div>
        <div class="location">Brooklyn, NY</div>
    </div>
</div>
<div class="date">Thursday, July 4, 2025</div>
<div class="letter-body">
    {html_body}
</div>
<div class="closing">Best wishes,</div>
<div class="signature-block">
    <span class="sig-name">Atma Degeyndt</span>
    <span class="sig-title">CMO, Growth Bastards Agency</span>
    <span class="sig-email">atma@growthbastards.com</span>
    <span class="sig-phone">(310) 494-1470</span>
</div>
</body>
</html>
"""
        pdf_options = {
            'encoding': "UTF-8",
            'margin-top': '1.3in',
            'margin-right': '1.3in',
            'margin-bottom': '1.3in',
            'margin-left': '1.3in'
        }
        pdfkit.from_string(html, pdf_path, options=pdf_options)
        print(f"[✓] Cover letter PDF created: {pdf_path}")
    except Exception as e:
        print(f"[✗] Cover letter PDF conversion failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf_cover.py <jobname>")
        sys.exit(1)

    jobname = sys.argv[1]
    txt_path = os.path.join("pipeline_output", f"{jobname}_coverletter.txt")
    pdf_path = os.path.join("pipeline_output", f"{jobname}_coverletter.pdf")

    if os.path.exists(txt_path):
        convert_markdown_txt_to_pdf(txt_path, pdf_path)
    else:
        print(f"[!] Cover letter .txt not found: {txt_path}")
