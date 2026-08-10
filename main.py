#!/usr/bin/env python3
"""
PDFtoAudio v2 — AI Audio & Podcast Studio
Convert PDF documents into Neural AI Audiobooks and 2-Host Podcasts.
"""

import sys
import argparse
import webbrowser
import uvicorn

from backend.pdf_parser import extract_pdf_info
from backend.tts_engine import synthesize_text_to_audio


def run_cli_mode(pdf_path: str, output_path: str = "audiobook.mp3", voice: str = "en-US-GuyNeural"):
    """Legacy CLI converter mode."""
    print(f"📖 Reading PDF file: {pdf_path}")
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        parsed = extract_pdf_info(pdf_bytes)
        print(f"✅ Extracted {parsed['metadata']['total_words']} words across {parsed['metadata']['total_pages']} pages.")
        print(f"🎙️ Synthesizing AI Audio using voice: {voice}...")

        import asyncio
        audio_bytes = asyncio.run(synthesize_text_to_audio(parsed["full_text"], voice=voice))

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        print(f"🎉 Audiobook saved successfully to '{output_path}'!")
    except Exception as e:
        print(f"❌ Error during conversion: {e}")


def main():
    parser = argparse.ArgumentParser(description="PDFtoAudio v2 — AI Audio & Podcast Studio")
    parser.add_argument("--cli", action="store_true", help="Run in command line converter mode")
    parser.add_argument("--pdf", type=str, help="Path to input PDF file for CLI mode")
    parser.add_argument("--output", type=str, default="audiobook.mp3", help="Output MP3 file path for CLI mode")
    parser.add_argument("--voice", type=str, default="en-US-GuyNeural", help="Neural Voice ID for CLI mode")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address for Web Studio server")
    parser.add_argument("--port", type=int, default=8000, help="Port number for Web Studio server")
    parser.add_argument("--no-browser", action="store_true", help="Do not open web browser automatically")

    args = parser.parse_args()

    if args.cli:
        if not args.pdf:
            # Fallback Tkinter dialog if --pdf not passed in --cli mode
            try:
                from tkinter.filedialog import askopenfilename
                args.pdf = askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
            except Exception:
                pass
        if not args.pdf:
            print("❌ Please provide a PDF file using --pdf <file.pdf>")
            sys.exit(1)
        run_cli_mode(args.pdf, args.output, args.voice)
    else:
        server_url = f"http://{args.host}:{args.port}"
        print("=" * 60)
        print("  🎧 PDFtoAudio v2 — AI Audio & Podcast Studio Server")
        print("=" * 60)
        print(f"  ➜ Server running at: {server_url}")
        print("  ➜ Press Ctrl+C to stop the server\n")

        if not args.no-browser:
            webbrowser.open(server_url)

        uvicorn.run("backend.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()