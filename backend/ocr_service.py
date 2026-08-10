import os

HAS_PYTESSERACT = False
try:
    import pytesseract
    from PIL import Image
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


def check_ocr_availability() -> dict:
    """Returns status of local OCR engine dependencies."""
    return {
        "pytesseract_installed": HAS_PYTESSERACT,
        "engine_message": "OCR Engine (Tesseract) is available." if HAS_PYTESSERACT else "Local Tesseract OCR library not detected. Install 'pytesseract' and tesseract binary for scanned image PDF processing."
    }


def perform_ocr_on_image_bytes(image_bytes: bytes) -> str:
    """Perform OCR on a single image byte buffer if available."""
    if not HAS_PYTESSERACT:
        return ""
    try:
        import io
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""
