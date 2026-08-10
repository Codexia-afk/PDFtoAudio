import os
import json
import uuid
import time
from typing import List, Optional, Dict, Any

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_storage")
DOCS_META_FILE = os.path.join(STORAGE_DIR, "documents.json")
NOTES_FILE = os.path.join(STORAGE_DIR, "bookmarks_notes.json")
STUDY_FILE = os.path.join(STORAGE_DIR, "study_materials.json")
CHAT_FILE = os.path.join(STORAGE_DIR, "chat_history.json")


def _ensure_storage():
    """Ensure data storage directory and JSON index files exist."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    for filepath in [DOCS_META_FILE, NOTES_FILE, STUDY_FILE, CHAT_FILE]:
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({}, f)


_ensure_storage()


def _read_json(filepath: str) -> Dict[str, Any]:
    _ensure_storage()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(filepath: str, data: Dict[str, Any]):
    _ensure_storage()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# --- Document Library Storage ---

def save_document(doc_meta: Dict[str, Any], doc_content: Dict[str, Any]):
    """Saves document metadata and extracted content."""
    doc_id = doc_meta["id"]
    docs = _read_json(DOCS_META_FILE)
    docs[doc_id] = doc_meta
    _write_json(DOCS_META_FILE, docs)

    # Save content JSON
    content_path = os.path.join(STORAGE_DIR, f"doc_{doc_id}.json")
    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(doc_content, f, indent=2)


def list_documents() -> List[Dict[str, Any]]:
    """Returns list of stored document metadata objects."""
    docs = _read_json(DOCS_META_FILE)
    return sorted(list(docs.values()), key=lambda x: x.get("created_at", 0), reverse=True)


def get_document_meta(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific document."""
    docs = _read_json(DOCS_META_FILE)
    return docs.get(doc_id)


def get_document_content(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get extracted text/content for a document."""
    content_path = os.path.join(STORAGE_DIR, f"doc_{doc_id}.json")
    if os.path.exists(content_path):
        with open(content_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def update_playback_position(doc_id: str, sentence_index: int, seconds: float):
    """Updates resume playback state for a document."""
    docs = _read_json(DOCS_META_FILE)
    if doc_id in docs:
        docs[doc_id]["last_played_sentence_index"] = sentence_index
        docs[doc_id]["last_played_seconds"] = seconds
        _write_json(DOCS_META_FILE, docs)


def delete_document(doc_id: str) -> bool:
    """Deletes document and associated files."""
    docs = _read_json(DOCS_META_FILE)
    if doc_id in docs:
        del docs[doc_id]
        _write_json(DOCS_META_FILE, docs)

        content_path = os.path.join(STORAGE_DIR, f"doc_{doc_id}.json")
        if os.path.exists(content_path):
            os.remove(content_path)
        return True
    return False


# --- Bookmarks & Notes Storage ---

def add_bookmark_note(doc_id: str, sentence_index: int, page_number: int, selected_text: str, note: str = "") -> Dict[str, Any]:
    notes_db = _read_json(NOTES_FILE)
    if doc_id not in notes_db:
        notes_db[doc_id] = []

    note_obj = {
        "id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "sentence_index": sentence_index,
        "page_number": page_number,
        "selected_text": selected_text,
        "note": note,
        "created_at": time.time()
    }
    notes_db[doc_id].append(note_obj)
    _write_json(NOTES_FILE, notes_db)
    return note_obj


def get_bookmarks_notes(doc_id: str) -> List[Dict[str, Any]]:
    notes_db = _read_json(NOTES_FILE)
    return notes_db.get(doc_id, [])


# --- Study Materials (Flashcards & Quizzes) Storage ---

def save_study_material(doc_id: str, material_type: str, data: Any):
    study_db = _read_json(STUDY_FILE)
    if doc_id not in study_db:
        study_db[doc_id] = {}
    study_db[doc_id][material_type] = data
    _write_json(STUDY_FILE, study_db)


def get_study_material(doc_id: str, material_type: str) -> Optional[Any]:
    study_db = _read_json(STUDY_FILE)
    return study_db.get(doc_id, {}).get(material_type)


# --- Chat History Storage ---

def save_chat_message(doc_id: str, sender: str, text: str, page_references: List[int], found_in_doc: bool) -> Dict[str, Any]:
    chat_db = _read_json(CHAT_FILE)
    if doc_id not in chat_db:
        chat_db[doc_id] = []

    msg = {
        "id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "sender": sender,
        "text": text,
        "page_references": page_references,
        "found_in_doc": found_in_doc,
        "created_at": time.time()
    }
    chat_db[doc_id].append(msg)
    _write_json(CHAT_FILE, chat_db)
    return msg


def get_chat_history(doc_id: str) -> List[Dict[str, Any]]:
    chat_db = _read_json(CHAT_FILE)
    return chat_db.get(doc_id, [])
