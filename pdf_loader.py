import os
import PyPDF2

def load_pdfs(pdf_folder="pdfs"):
    texts = ""
    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            path = os.path.join(pdf_folder, file)
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    texts += page.extract_text() + "\n"
    return texts
