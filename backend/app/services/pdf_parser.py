import io
import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False

# A page with fewer real characters than this is treated as "no usable
# text layer" (e.g. a scanned page saved as an image) and gets OCR'd.
_MIN_TEXT_CHARS = 20

# Render pages at this zoom before OCR — higher = better accuracy, slower.
_OCR_ZOOM = 2.0


def _ocr_page(page) -> str:
    """Render a PDF page to an image and run OCR on it. Returns '' on any failure
    (missing Tesseract binary, corrupt page, etc.) rather than raising, so a single
    bad/scanned page never takes down the whole upload."""
    if not _OCR_AVAILABLE:
        return ""
    try:
        matrix = fitz.Matrix(_OCR_ZOOM, _OCR_ZOOM)
        pix = page.get_pixmap(matrix=matrix)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception:
        # Most commonly: the Tesseract binary isn't installed on this machine.
        # We swallow the error here and let extract_text_from_pdf's caller
        # decide what to do with an empty page rather than crashing the request.
        return ""


def extract_text_from_pdf(pdf_path: str):

    doc = fitz.open(pdf_path)

    full_text = ""

    for page_num, page in enumerate(doc):

        text = page.get_text()

        # No (or barely any) embedded text layer -> likely a scanned image page.
        # Fall back to OCR so scanned RFPs still get analyzed instead of
        # silently producing an empty document.
        if len(text.strip()) < _MIN_TEXT_CHARS:
            ocr_text = _ocr_page(page)
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text

        full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
        full_text += text

    return full_text