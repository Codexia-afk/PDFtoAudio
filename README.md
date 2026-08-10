# 🎧 PDFtoAudio v2 — AI Audio & Podcast Studio

> Convert PDF documents into hyper-realistic **Neural AI Audiobooks** and engaging **2-Host AI Podcasts** with live sentence-synced text highlighting.

![PDFtoAudio v2 Banner](asset/Screenshot.png)

---

## ✨ What's New in v2.0

* 🎙️ **Hyper-Realistic Neural AI Voices**: Built-in support for **50+ Microsoft Neural AI voices** (`edge-tts`) across English, Hindi, Bengali, Spanish, French, German, Japanese, and more.
* 📻 **AI Podcast Mode**: Automatically transforms long PDF documents into an entertaining **2-host conversational podcast show** hosted by Alex and Sam!
* 📖 **Smart PDF & Chapter Parser**: Powered by `PyMuPDF` (`fitz`) to extract clean text while filtering out header/footer noise, page numbers, and inline citation clutter.
* 🎛️ **Modern Glassmorphism Web Studio UI**: Features a side-by-side interactive PDF reader and audio studio with real-time waveform visualizers.
* 🎤 **Karaoke / Live Sentence Sync**: Sentence-by-sentence text highlighting synced directly with spoken audio playback.
* ⚡ **Playback Speed & Custom Scope**: Adjustable playback speeds (0.75x to 2.0x) and chapter-by-chapter or full document conversion.
* 📑 **Caption Exports**: One-click generation and export of `.VTT` and `.SRT` subtitle files.
* 💻 **Dual Mode (Web UI + CLI)**: Run as a full web app studio or run directly from the command line.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.14, FastAPI, Uvicorn, PyMuPDF (`fitz`), PyPDF2
* **Audio & Speech**: `edge-tts` (Microsoft Neural AI), `gTTS`
* **Frontend**: HTML5, Vanilla CSS3 (Dark Glassmorphism Design System), JavaScript (ES6+), Canvas API
* **Deployment**: Uvicorn ASGI Server

---

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Codexia-afk/PDFtoAudio.git
   cd PDFtoAudio
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Quick Start

### 🌐 Option A: Launch Web Studio (Recommended)

Run the unified launcher:

```bash
python main.py
```

This will automatically launch the Web Studio server at `http://127.0.0.1:8000` and open your default web browser!

### 💻 Option B: Legacy CLI Mode

To convert a PDF directly to audio from the terminal:

```bash
python main.py --cli --pdf document.pdf --output my_audiobook.mp3 --voice en-US-GuyNeural
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the Web Studio UI |
| `GET` | `/api/voices` | Returns JSON list of available AI voices |
| `POST` | `/api/upload-pdf` | Upload PDF file & extract chapters, metadata, sentences |
| `POST` | `/api/tts` | Synthesize neural TTS audio stream (`audio/mpeg`) |
| `POST` | `/api/podcast` | Synthesize 2-host podcast audio episode |
| `POST` | `/api/export-subtitles` | Generate downloadable `.VTT` or `.SRT` captions |

---

## 🤝 Contributing

Contributions, feature requests, and pull requests are always welcome! Feel free to check the issues page.

---

## 📄 License

Distributed under the MIT License. Developed by **Codexia_afk**.
