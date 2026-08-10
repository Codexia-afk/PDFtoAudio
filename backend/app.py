import os
import io
import uuid
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.parser_service import parse_document
from backend.storage_service import (
    save_document, list_documents, get_document_meta, get_document_content,
    update_playback_position, delete_document, add_bookmark_note, get_bookmarks_notes,
    save_study_material, get_study_material, save_chat_message, get_chat_history
)
from backend.summary_service import generate_document_summary
from backend.quiz_service import generate_flashcards, generate_quiz_questions, export_flashcards_anki_csv
from backend.chat_service import answer_document_question
from backend.export_service import generate_rss_podcast_feed
from backend.tts_engine import get_available_voices, synthesize_text_to_audio
from backend.podcast_engine import generate_podcast_script, synthesize_podcast_audio

app = FastAPI(title="PDFtoAudio - AI Learning & Accessible Document Platform", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>PDFtoAudio Backend Running</h1>")


@app.get("/api/voices")
async def list_voices():
    return JSONResponse(content={"voices": get_available_voices()})


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload document, extract text/chapters/citations, and store in Library."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Size limit check (50MB)
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum size limit (50MB).")

    doc_id = str(uuid.uuid4())
    parsed_data = parse_document(contents, file.filename)

    meta = {
        "id": doc_id,
        "filename": file.filename,
        "file_type": file.filename.rsplit(".", 1)[-1].lower(),
        "title": parsed_data["metadata"]["title"],
        "total_pages": parsed_data["metadata"]["total_pages"],
        "total_words": parsed_data["metadata"]["total_words"],
        "estimated_minutes": parsed_data["metadata"]["estimated_minutes"],
        "created_at": time.time(),
        "last_played_sentence_index": 0,
        "last_played_seconds": 0.0,
        "quality_report": parsed_data["metadata"]["quality_report"]
    }

    content_data = {
        "doc_id": doc_id,
        "full_text": parsed_data["full_text"],
        "pages": parsed_data["pages"],
        "chapters": parsed_data["chapters"],
        "sentences": parsed_data["sentences"]
    }

    save_document(meta, content_data)
    return JSONResponse(content={"metadata": meta, "content": content_data})


@app.post("/api/upload-pdf")
async def upload_pdf_legacy(file: UploadFile = File(...)):
    """Legacy alias endpoint for backward compatibility."""
    return await upload_document(file)


@app.get("/api/documents")
async def get_library_documents():
    """List all documents in Library."""
    docs = list_documents()
    return JSONResponse(content={"documents": docs})


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Retrieve metadata and extracted content for a document."""
    meta = get_document_meta(doc_id)
    content = get_document_content(doc_id)
    if not meta or not content:
        raise HTTPException(status_code=404, detail="Document not found.")
    return JSONResponse(content={"metadata": meta, "content": content})


@app.post("/api/documents/{doc_id}/playback")
async def save_playback(doc_id: str, sentence_index: int = Form(0), seconds: float = Form(0.0)):
    """Update last played sentence index and timestamp."""
    update_playback_position(doc_id, sentence_index, seconds)
    return JSONResponse(content={"status": "updated"})


@app.delete("/api/documents/{doc_id}")
async def remove_document(doc_id: str):
    """Delete document from Library."""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return JSONResponse(content={"status": "deleted"})


@app.post("/api/documents/{doc_id}/bookmarks")
async def create_bookmark(
    doc_id: str,
    sentence_index: int = Form(...),
    page_number: int = Form(...),
    selected_text: str = Form(...),
    note: str = Form("")
):
    """Save bookmark or note."""
    bookmark = add_bookmark_note(doc_id, sentence_index, page_number, selected_text, note)
    return JSONResponse(content={"bookmark": bookmark})


@app.get("/api/documents/{doc_id}/bookmarks")
async def list_bookmarks(doc_id: str):
    """List bookmarks and notes for a document."""
    bookmarks = get_bookmarks_notes(doc_id)
    return JSONResponse(content={"bookmarks": bookmarks})


@app.post("/api/documents/{doc_id}/summary")
async def get_summary(doc_id: str, mode: str = Form("overview")):
    """Generate educational summary across 6 modes."""
    content = get_document_content(doc_id)
    if not content:
        raise HTTPException(status_code=404, detail="Document not found.")

    summary = generate_document_summary(content["full_text"], content["sentences"], mode=mode)
    return JSONResponse(content=summary)


@app.post("/api/documents/{doc_id}/study")
async def get_study_materials(doc_id: str):
    """Generate flashcards and multiple-choice quizzes."""
    content = get_document_content(doc_id)
    if not content:
        raise HTTPException(status_code=404, detail="Document not found.")

    flashcards = get_study_material(doc_id, "flashcards")
    quizzes = get_study_material(doc_id, "quizzes")

    if not flashcards:
        flashcards = generate_flashcards(content["sentences"])
        save_study_material(doc_id, "flashcards", flashcards)

    if not quizzes:
        quizzes = generate_quiz_questions(content["sentences"])
        save_study_material(doc_id, "quizzes", quizzes)

    return JSONResponse(content={"flashcards": flashcards, "quizzes": quizzes})


@app.get("/api/documents/{doc_id}/anki-csv")
async def export_anki_csv(doc_id: str):
    """Download flashcards in Anki CSV format."""
    flashcards = get_study_material(doc_id, "flashcards")
    if not flashcards:
        content = get_document_content(doc_id)
        if not content:
            raise HTTPException(status_code=404, detail="Document not found.")
        flashcards = generate_flashcards(content["sentences"])

    csv_data = export_flashcards_anki_csv(flashcards)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=flashcards_{doc_id[:8]}.csv"}
    )


@app.post("/api/documents/{doc_id}/chat")
async def document_chat(doc_id: str, query: str = Form(...)):
    """Grounded Q&A chat about document with page citations."""
    content = get_document_content(doc_id)
    if not content:
        raise HTTPException(status_code=404, detail="Document not found.")

    res = answer_document_question(query, content["sentences"], content["full_text"])
    save_chat_message(doc_id, "user", query, [], True)
    msg = save_chat_message(doc_id, "assistant", res["answer"], res["page_references"], res["found_in_doc"])
    return JSONResponse(content=msg)


@app.get("/api/documents/{doc_id}/chat")
async def get_chat_logs(doc_id: str):
    """Get chat message history for document."""
    history = get_chat_history(doc_id)
    return JSONResponse(content={"history": history})


@app.post("/api/tts")
async def generate_tts(
    text: str = Form(...),
    voice: str = Form("en-US-GuyNeural"),
    rate: str = Form("+0%")
):
    try:
        audio_bytes = await synthesize_text_to_audio(text=text, voice=voice, rate=rate)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=audiobook.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Generation failed: {str(e)}")


@app.post("/api/podcast")
async def generate_podcast(text: str = Form(...)):
    try:
        script = generate_podcast_script(text)
        audio_bytes = await synthesize_podcast_audio(script)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=podcast_episode.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Podcast synthesis failed: {str(e)}")


@app.get("/api/documents/{doc_id}/rss")
async def get_podcast_rss(doc_id: str):
    """Get Podcast RSS Feed XML for document."""
    meta = get_document_meta(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found.")

    audio_url = f"http://127.0.0.1:8000/api/podcast"
    feed_xml = generate_rss_podcast_feed(doc_id, meta["title"], audio_url)
    return Response(content=feed_xml, media_type="application/rss+xml")


@app.post("/api/export-subtitles")
async def export_subtitles(text: str = Form(...), format_type: str = Form("vtt")):
    lines = text.split("\n")
    subtitle_content = "WEBVTT\n\n" if format_type == "vtt" else ""
    current_time = 0.0

    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        duration = max(2.0, len(line.split()) * 0.4)
        start_min, start_sec = divmod(current_time, 60)
        end_min, end_sec = divmod(current_time + duration, 60)

        if format_type == "vtt":
            start_str = f"00:{int(start_min):02d}:{start_sec:06.3f}"
            end_str = f"00:{int(end_min):02d}:{end_sec:06.3f}"
            subtitle_content += f"{start_str} --> {end_str}\n{line}\n\n"
        else:
            start_str = f"00:{int(start_min):02d}:{int(start_sec):02d},000"
            end_str = f"00:{int(end_min):02d}:{int(end_sec):02d},000"
            subtitle_content += f"{i}\n{start_str} --> {end_str}\n{line}\n\n"

        current_time += duration

    ext = "vtt" if format_type == "vtt" else "srt"
    return Response(
        content=subtitle_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=captions.{ext}"}
    )
