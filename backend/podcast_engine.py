import re
import asyncio
import tempfile
import os
from backend.tts_engine import generate_speech_edge_tts


def generate_podcast_script(pdf_text: str, max_turns: int = 10):
    """
    Transforms PDF text into a 2-host conversational podcast script.
    Host A: Alex (Lead Host / Presenter)
    Host B: Sam (Co-Host / Inquirer)
    """
    # Clean and extract main sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', pdf_text) if len(s.strip()) > 15]
    if not sentences:
        sentences = ["This document contains interesting insights that we are exploring today."]

    script_turns = []

    # Intro turn
    script_turns.append({
        "speaker": "Alex",
        "voice": "en-US-AndrewNeural",
        "text": "Welcome back everyone to the PDF Deep Dive podcast! Today we are discussing an insightful document that was just uploaded."
    })
    script_turns.append({
        "speaker": "Sam",
        "voice": "en-US-AvaNeural",
        "text": "Thanks Alex! I've been reviewing the pages, and there are some fascinating takeaways here. Where should we kick things off?"
    })

    # Group sentences into chunks for dynamic discussion
    chunk_size = max(1, len(sentences) // min(max_turns, max(1, len(sentences))))
    for i in range(0, min(len(sentences), max_turns * chunk_size), chunk_size):
        chunk = " ".join(sentences[i:i + chunk_size])

        if i % 2 == 0:
            script_turns.append({
                "speaker": "Alex",
                "voice": "en-US-AndrewNeural",
                "text": f"One key section highlights that {chunk}"
            })
            script_turns.append({
                "speaker": "Sam",
                "voice": "en-US-AvaNeural",
                "text": "That's a super interesting point. It really changes how we think about this topic."
            })
        else:
            script_turns.append({
                "speaker": "Sam",
                "voice": "en-US-AvaNeural",
                "text": f"Furthermore, the document explains that {chunk}"
            })
            script_turns.append({
                "speaker": "Alex",
                "voice": "en-US-AndrewNeural",
                "text": "Exactly. This leads into the broader conclusions drawn by the author."
            })

    # Outro turn
    script_turns.append({
        "speaker": "Alex",
        "voice": "en-US-AndrewNeural",
        "text": "That wraps up our quick episode on this document! Thank you all for listening to PDF Deep Dive."
    })

    return script_turns


async def synthesize_podcast_audio(script_turns: list) -> bytes:
    """
    Synthesizes each turn with its respective speaker voice and combines into a single MP3 stream.
    """
    audio_segments = []

    for turn in script_turns:
        text = turn["text"]
        voice = turn.get("voice", "en-US-AndrewNeural")
        try:
            segment_bytes = await generate_speech_edge_tts(text=text, voice=voice)
            if segment_bytes:
                audio_segments.append(segment_bytes)
        except Exception as e:
            print(f"Error generating podcast segment for {turn['speaker']}: {e}")

    # Concatenate all MP3 byte chunks
    combined_audio = b"".join(audio_segments)
    return combined_audio
