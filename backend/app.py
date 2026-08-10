import os
import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.pdf_parser import extract_pdf_info
from backend.tts_engine import get_available_voices, synthesize_text_to_audio
from backend.podcast_engine import generate_podcast_script, synthesize_podcast_audio

app = FastAPI(title="PDFtoAudio v2 - AI Audio & Podcast Studio", version="2.0.0")

# Enable CORS for local dev / client integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend directory if exists
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>PDFtoAudio v2 Backend Running</h1>")


@app.get("/api/voices")
async def list_voices():
    """Returns available AI neural voices."""
    return JSONResponse(content={"voices": get_available_voices()})


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF file and extract text, chapters, sentences, and metadata."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        parsed_data = extract_pdf_info(contents)
        parsed_data["filename"] = file.filename
        return JSONResponse(content=parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@app.post("/api/tts")
async def generate_tts(
    text: str = Form(...),
    voice: str = Form("en-US-GuyNeural"),
    rate: str = Form("+0%")
):
    """Generate neural TTS audio stream for provided text."""
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
    """Generate 2-host AI Podcast dialogue and combined audio stream."""
    try:
        script = generate_podcast_script(pdf_text=text)
        audio_bytes = await synthesize_podcast_audio(script)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=podcast_episode.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Podcast synthesis failed: {str(e)}")


@app.post("/api/export-subtitles")
async def export_subtitles(text: str = Form(...), format_type: str = Form("vtt")):
    """Generate subtitle captions (VTT or SRT) for the document text."""
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
