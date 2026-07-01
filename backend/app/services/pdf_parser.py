import fitz

def extract_text_from_pdf(pdf_path: str):

    doc = fitz.open(pdf_path)

    full_text = ""

    for page_num, page in enumerate(doc):

        text = page.get_text()

        full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"

        full_text += text

    return full_text