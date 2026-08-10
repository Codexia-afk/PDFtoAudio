import re
import io
import pymupdf  # PyMuPDF
from typing import Dict, Any, List

from backend.ocr_service import check_ocr_availability


def clean_line_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\r\n|\r', '\n', text)
    # Remove header/footer line patterns like "Page 1 of 10" or "Page 1"
    text = re.sub(r'Page\s+\d+(\s+of\s+\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def parse_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Multi-format document parser (PDF, DOCX, TXT, MD, EPUB).
    Returns text by page, chapters, sentences, and Parser Quality Report.
    """
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    pages_data = []
    scanned_pages_count = 0
    warnings = []

    if ext == "pdf":
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            for page_num, page in enumerate(doc, start=1):
                p_text = clean_line_text(page.get_text("text"))

                # Check if page is image-scanned (has image drawing rects but near 0 text)
                images = page.get_images()
                if len(p_text.strip()) < 30 and len(images) > 0:
                    scanned_pages_count += 1

                pages_data.append({
                    "page_number": page_num,
                    "text": p_text,
                    "has_images": len(images) > 0
                })
        except Exception as e:
            warnings.append(f"PyMuPDF parsing warning: {str(e)}")
            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                for page_num, page in enumerate(reader.pages, start=1):
                    p_text = clean_line_text(page.extract_text() or "")
                    pages_data.append({
                        "page_number": page_num,
                        "text": p_text,
                        "has_images": False
                    })
            except Exception as e2:
                warnings.append(f"PyPDF2 fallback failed: {str(e2)}")

    elif ext == "docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            full_docx = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
            pages_data.append({"page_number": 1, "text": clean_line_text(full_docx), "has_images": False})
        except Exception:
            # Fallback raw text decode
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            pages_data.append({"page_number": 1, "text": clean_line_text(raw_text), "has_images": False})

    else:
        # TXT / MD / HTML / EPUB text decode
        raw_text = file_bytes.decode("utf-8", errors="ignore")
        pages_data.append({"page_number": 1, "text": clean_line_text(raw_text), "has_images": False})

    # Combine full text & build page mapping index
    full_text = "\n\n".join(p["text"] for p in pages_data if p["text"])
    total_pages = max(1, len(pages_data))

    # Detect language simple check
    detected_lang = "en"
    if re.search(r'[\u0900-\u097F]', full_text):
        detected_lang = "hi"
    elif re.search(r'[\u0980-\u09FF]', full_text):
        detected_lang = "bn"
    elif re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', full_text):
        detected_lang = "ja"

    ocr_required = scanned_pages_count > 0 and (scanned_pages_count / total_pages) > 0.4
    if ocr_required:
        warnings.append(f"Scanned images detected on {scanned_pages_count} page(s). OCR recommended for complete text extraction.")

    ocr_status = check_ocr_availability()

    quality_report = {
        "total_pages": total_pages,
        "scanned_pages_count": scanned_pages_count,
        "ocr_required": ocr_required,
        "ocr_available": ocr_status["pytesseract_installed"],
        "ocr_message": ocr_status["engine_message"],
        "detected_language": detected_lang,
        "warnings": warnings,
        "has_tables_or_math": bool(re.search(r'[\+\=\/\*]\s*\d+|\b(table|fig|figure|equation)\b', full_text, re.IGNORECASE))
    }

    # Chapter Detection with Page Number Association
    chapters = []
    current_ch_title = "Chapter 1: Overview"
    current_ch_lines = []
    current_start_page = 1
    chapter_index = 1

    for p in pages_data:
        p_num = p["page_number"]
        lines = p["text"].split("\n")
        for line in lines:
            stripped = line.strip()
            is_heading = bool(re.match(r'^(chapter|section|part)\s+\d+|^[I|V|X]+\.\s+', stripped, re.IGNORECASE))
            if is_heading and current_ch_lines:
                chapters.append({
                    "id": chapter_index,
                    "title": current_ch_title,
                    "start_page": current_start_page,
                    "end_page": p_num,
                    "text": "\n".join(current_ch_lines).strip()
                })
                chapter_index += 1
                current_ch_title = stripped.capitalize()
                current_ch_lines = []
                current_start_page = p_num
            else:
                if stripped:
                    current_ch_lines.append(stripped)

    if current_ch_lines or not chapters:
        chapters.append({
            "id": chapter_index,
            "title": current_ch_title if len(chapters) > 0 else "Full Document",
            "start_page": current_start_page,
            "end_page": total_pages,
            "text": "\n".join(current_ch_lines).strip() if current_ch_lines else full_text
        })

    # Sentence Splitting with Page Citation mapping
    sentences = []
    sentence_counter = 1
    char_offset = 0

    for p in pages_data:
        p_num = p["page_number"]
        p_sentences = re.split(r'(?<=[.!?])\s+', p["text"])
        for s in p_sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            word_count = len(s_clean.split())
            est_duration = max(1.5, round(word_count / 2.5, 2))
            sentences.append({
                "id": sentence_counter,
                "page_number": p_num,
                "text": s_clean,
                "start_offset": char_offset,
                "end_offset": char_offset + len(s_clean),
                "estimated_seconds": est_duration
            })
            sentence_counter += 1
            char_offset += len(s_clean) + 1

    total_words = len(full_text.split())
    estimated_minutes = max(1, round(total_words / 150))

    return {
        "metadata": {
            "title": filename.rsplit(".", 1)[0].replace("_", " ").title(),
            "total_pages": total_pages,
            "total_characters": len(full_text),
            "total_words": total_words,
            "estimated_minutes": estimated_minutes,
            "quality_report": quality_report
        },
        "pages": pages_data,
        "full_text": full_text,
        "chapters": chapters,
        "sentences": sentences
    }
