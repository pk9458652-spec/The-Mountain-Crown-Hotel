import markdown
from xhtml2pdf import pisa
import sys

def convert_md_to_pdf(md_file_path, pdf_file_path):
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
            
        html_text = markdown.markdown(md_text, extensions=['extra', 'tables'])
        
        full_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: a4; margin: 2cm; }}
                body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12pt; line-height: 1.5; color: #333; }}
                h1 {{ color: #d4af37; font-size: 24pt; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 20px; }}
                h2 {{ color: #1e293b; font-size: 16pt; margin-top: 25px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
                h3 {{ color: #1e293b; font-size: 14pt; margin-top: 15px; }}
                p, li {{ margin-bottom: 10px; }}
                ul {{ margin-left: 20px; }}
                strong {{ color: #000; }}
            </style>
        </head>
        <body>
            {html_text}
        </body>
        </html>
        """

        with open(pdf_file_path, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(full_html, dest=result_file)

        if pisa_status.err:
            print("Error generating PDF")
            sys.exit(1)
        else:
            print(f"PDF generated successfully at: {pdf_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    md_path = r"C:\Users\saksh\.gemini\antigravity\brain\6c316d31-f171-4e3f-8469-b188de4d84c0\simple_project_report.md"
    pdf_path = r"C:\Users\saksh\.gemini\antigravity\brain\6c316d31-f171-4e3f-8469-b188de4d84c0\simple_project_report.pdf"
    convert_md_to_pdf(md_path, pdf_path)
