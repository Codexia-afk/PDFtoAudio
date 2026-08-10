import unittest
import json
import os
import sys
import pymupdf

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.parser_service import parse_document
from backend.storage_service import save_document, list_documents, update_playback_position, add_bookmark_note, delete_document
from backend.summary_service import generate_document_summary
from backend.quiz_service import generate_flashcards, generate_quiz_questions, export_flashcards_anki_csv
from backend.chat_service import answer_document_question
from backend.export_service import generate_rss_podcast_feed
from backend.ocr_service import check_ocr_availability


class TestPDFtoAudioPlatform(unittest.TestCase):

    def setUp(self):
        # Create a real in-memory PDF using PyMuPDF
        doc = pymupdf.open()
        page1 = doc.new_page()
        page1.insert_text((50, 50), "Chapter 1: Introduction to Quantum Mechanics.\nQuantum mechanics is a fundamental theory in physics that provides a description of physical properties at atomic scale.")
        page2 = doc.new_page()
        page2.insert_text((50, 50), "Chapter 2: Key Principles.\nKey Principle 1 demonstrates wave-particle duality. Light behaves as wave and photons.")

        self.pdf_bytes = doc.tobytes()
        doc.close()
        self.filename = "test_quantum.pdf"

    def test_document_parser(self):
        result = parse_document(self.pdf_bytes, self.filename)
        self.assertIn("metadata", result)
        self.assertIn("chapters", result)
        self.assertIn("sentences", result)
        self.assertGreaterEqual(result["metadata"]["total_words"], 20)
        self.assertGreaterEqual(len(result["sentences"]), 2)

    def test_storage_service(self):
        parsed = parse_document(self.pdf_bytes, self.filename)
        doc_id = "test-doc-123"
        meta = {
            "id": doc_id,
            "filename": self.filename,
            "title": "Test Document",
            "total_pages": 2,
            "total_words": 100,
            "estimated_minutes": 1,
            "created_at": 1000.0,
            "last_played_sentence_index": 0,
            "last_played_seconds": 0.0,
            "quality_report": parsed["metadata"]["quality_report"]
        }
        save_document(meta, parsed)

        docs = list_documents()
        self.assertTrue(any(d["id"] == doc_id for d in docs))

        update_playback_position(doc_id, 3, 12.5)
        bm = add_bookmark_note(doc_id, 2, 1, "Quantum mechanics", "Important concept")
        self.assertEqual(bm["doc_id"], doc_id)

        deleted = delete_document(doc_id)
        self.assertTrue(deleted)

    def test_summary_service(self):
        parsed = parse_document(self.pdf_bytes, self.filename)
        modes = ["overview", "strict", "deep_dive", "explain_simply", "professor", "feynman"]
        for m in modes:
            summary = generate_document_summary(parsed["full_text"], parsed["sentences"], mode=m)
            self.assertEqual(summary["mode"], m)
            self.assertTrue(len(summary["executive_summary"]) > 10)

    def test_quiz_and_flashcards(self):
        parsed = parse_document(self.pdf_bytes, self.filename)
        flashcards = generate_flashcards(parsed["sentences"])
        quizzes = generate_quiz_questions(parsed["sentences"])

        self.assertIsInstance(flashcards, list)
        self.assertIsInstance(quizzes, list)

        if flashcards:
            csv_output = export_flashcards_anki_csv(flashcards)
            self.assertIn("Front,Back,PageReference", csv_output)

    def test_document_chat(self):
        parsed = parse_document(self.pdf_bytes, self.filename)
        res_found = answer_document_question("quantum mechanics", parsed["sentences"], parsed["full_text"])
        self.assertTrue(res_found["found_in_doc"])
        self.assertGreaterEqual(len(res_found["page_references"]), 1)

        res_not_found = answer_document_question("astrophysics galaxies black holes", parsed["sentences"], parsed["full_text"])
        self.assertFalse(res_not_found["found_in_doc"])

    def test_export_rss(self):
        feed = generate_rss_podcast_feed("doc-1", "Quantum Mechanics Episode", "http://localhost:8000/audio.mp3")
        self.assertIn("<rss version=\"2.0\"", feed)
        self.assertIn("<title>PDFtoAudio Studio — Quantum Mechanics Episode</title>", feed)

    def test_ocr_availability(self):
        ocr_info = check_ocr_availability()
        self.assertIn("pytesseract_installed", ocr_info)


if __name__ == "__main__":
    unittest.main()
