import re
import pymupdf  # PyMuPDF


def clean_text(text: str) -> str:
    """Clean extracted PDF text by removing excessive whitespace and common noise."""
    if not text:
        return ""
    # Normalize newline sequences
    text = re.sub(r'\r\n|\r', '\n', text)
    # Remove header/footer line patterns like "Page 1 of 10"
    text = re.sub(r'Page\s+\d+(\s+of\s+\d+)?', '', text, flags=re.IGNORECASE)
    # Replace multiple empty lines with double newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Replace horizontal whitespace sequences with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_pdf_info(pdf_bytes: bytes):
    """
    Extract text, chapters, sentences, and metadata from a PDF file buffer.
    """
    pages_text = []

    # Try PyMuPDF first
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            p_text = page.get_text("text")
            pages_text.append(clean_text(p_text))
    except Exception as e:
        print(f"PyMuPDF error: {e}, attempting PyPDF fallback...")
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                p_text = page.extract_text() or ""
                pages_text.append(clean_text(p_text))
        except Exception:
            pass

    full_text = "\n\n".join(p for p in pages_text if p)
    total_pages = len(pages_text)

    # Detect Chapters
    chapters = []
    current_chapter_title = "Chapter 1: Introduction"
    current_chapter_lines = []

    lines = full_text.split('\n')
    chapter_index = 1

    for line in lines:
        stripped = line.strip()
        is_heading = bool(re.match(r'^(chapter|section|part)\s+\d+|^[I|V|X]+\.\s+', stripped, re.IGNORECASE))
        if is_heading and current_chapter_lines:
            chapters.append({
                "id": chapter_index,
                "title": current_chapter_title,
                "text": "\n".join(current_chapter_lines).strip()
            })
            chapter_index += 1
            current_chapter_title = stripped.capitalize()
            current_chapter_lines = []
        else:
            if stripped:
                current_chapter_lines.append(stripped)

    if current_chapter_lines or not chapters:
        chapters.append({
            "id": chapter_index,
            "title": current_chapter_title if len(chapters) > 0 else "Full Document",
            "text": "\n".join(current_chapter_lines).strip() if current_chapter_lines else full_text
        })

    # Break full text into sentence chunks for sync/karaoke highlighting
    raw_sentences = re.split(r'(?<=[.!?])\s+', full_text)
    sentences = []
    char_offset = 0

    for i, s in enumerate(raw_sentences):
        s_clean = s.strip()
        if not s_clean:
            continue
        word_count = len(s_clean.split())
        est_duration = max(1.5, round(word_count / 2.5, 2))
        sentences.append({
            "id": i + 1,
            "text": s_clean,
            "start_offset": char_offset,
            "end_offset": char_offset + len(s_clean),
            "estimated_seconds": est_duration
        })
        char_offset += len(s_clean) + 1

    word_count = len(full_text.split())
    estimated_reading_minutes = max(1, round(word_count / 150))

    return {
        "metadata": {
            "total_pages": total_pages,
            "total_characters": len(full_text),
            "total_words": word_count,
            "estimated_minutes": estimated_reading_minutes
        },
        "full_text": full_text,
        "chapters": chapters,
        "sentences": sentences
    }
