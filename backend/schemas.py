from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time


class PageSnippet(BaseModel):
    page_number: int
    text: str
    has_ocr: bool = False


class SentenceItem(BaseModel):
    id: int
    page_number: int = 1
    text: str
    start_offset: int = 0
    end_offset: int = 0
    estimated_seconds: float = 2.0


class ChapterItem(BaseModel):
    id: int
    title: str
    start_page: int = 1
    end_page: int = 1
    text: str


class ParserQualityReport(BaseModel):
    total_pages: int = 0
    scanned_pages_count: int = 0
    ocr_required: bool = False
    detected_language: str = "en"
    warnings: List[str] = []
    has_tables_or_math: bool = False


class DocumentMeta(BaseModel):
    id: str
    filename: str
    file_type: str = "pdf"
    title: str
    author: Optional[str] = "Unknown"
    total_pages: int = 1
    total_words: int = 0
    estimated_minutes: int = 1
    created_at: float = Field(default_factory=time.time)
    last_played_sentence_index: int = 0
    last_played_seconds: float = 0.0
    quality_report: ParserQualityReport = Field(default_factory=ParserQualityReport)


class BookmarkNote(BaseModel):
    id: str
    doc_id: str
    sentence_index: int
    page_number: int
    selected_text: str
    note: str = ""
    created_at: float = Field(default_factory=time.time)


class Flashcard(BaseModel):
    id: str
    doc_id: str
    front: str
    back: str
    page_reference: int = 1
    difficulty: str = "medium"


class QuizQuestion(BaseModel):
    id: str
    doc_id: str
    question: str
    options: List[str] = []
    correct_option_index: int = 0
    explanation: str = ""
    page_reference: int = 1


class ChatMessage(BaseModel):
    id: str
    doc_id: str
    sender: str  # "user" or "assistant"
    text: str
    page_references: List[int] = []
    found_in_doc: bool = True
    created_at: float = Field(default_factory=time.time)


class SummaryResponse(BaseModel):
    mode: str
    title: str
    executive_summary: str
    key_takeaways: List[Dict[str, Any]] = []
    glossary: List[Dict[str, str]] = []
    chapter_outlines: List[Dict[str, Any]] = []
