import re
import asyncio
import tempfile
import os
from backend.tts_engine import generate_speech_edge_tts


def generate_podcast_script(sentences_data: list, max_turns: int = 8):
    """
    Transforms PDF sentence objects into a 2-host conversational podcast script with page citations.
    Host A: Alex (Male Storyteller)
    Host B: Sam (Female Studio Host)
    """
    if not sentences_data:
        sentences_data = [{"text": "This document contains insightful facts.", "page_number": 1}]

    # Convert raw text strings to sentence objects if necessary
    if isinstance(sentences_data, str):
        sentences_data = [{"text": s.strip(), "page_number": 1} for s in re.split(r'(?<=[.!?])\s+', sentences_data) if len(s.strip()) > 15]

    script_turns = []

    # Intro turn
    script_turns.append({
        "speaker": "Alex",
        "voice": "en-US-AndrewNeural",
        "text": "Welcome to PDFtoAudio Deep Dive podcast! Today we are reviewing an uploaded document.",
        "page_reference": 1
    })
    script_turns.append({
        "speaker": "Sam",
        "voice": "en-US-AvaNeural",
        "text": "Thanks Alex! Let's examine the main findings and page references in detail.",
        "page_reference": 1
    })

    chunk_size = max(1, len(sentences_data) // min(max_turns, max(1, len(sentences_data))))
    for i in range(0, min(len(sentences_data), max_turns * chunk_size), chunk_size):
        chunk_items = sentences_data[i:i + chunk_size]
        chunk_text = " ".join(s["text"] for s in chunk_items)
        page_num = chunk_items[0].get("page_number", 1)

        if i % 2 == 0:
            script_turns.append({
                "speaker": "Alex",
                "voice": "en-US-AndrewNeural",
                "text": f"According to Page {page_num}: {chunk_text}",
                "page_reference": page_num
            })
            script_turns.append({
                "speaker": "Sam",
                "voice": "en-US-AvaNeural",
                "text": f"That's a key takeaway from Page {page_num}. It directly supports the core topic.",
                "page_reference": page_num
            })
        else:
            script_turns.append({
                "speaker": "Sam",
                "voice": "en-US-AvaNeural",
                "text": f"Moving to section on Page {page_num}: {chunk_text}",
                "page_reference": page_num
            })
            script_turns.append({
                "speaker": "Alex",
                "voice": "en-US-AndrewNeural",
                "text": f"Exactly. That sums up the key conclusion on Page {page_num}.",
                "page_reference": page_num
            })

    # Outro turn
    script_turns.append({
        "speaker": "Alex",
        "voice": "en-US-AndrewNeural",
        "text": "That concludes our educational overview for this episode. Thank you for listening!",
        "page_reference": sentences_data[-1].get("page_number", 1) if sentences_data else 1
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
