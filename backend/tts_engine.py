import asyncio
import os
import tempfile
import edge_tts
from gtts import gTTS

# Comprehensive list of high-definition Microsoft Neural AI voices & gTTS fallbacks
AVAILABLE_VOICES = [
    # English Voices
    {"id": "en-US-GuyNeural", "name": "Guy (US - Male / Natural)", "lang": "en-US", "gender": "Male", "provider": "edge-tts"},
    {"id": "en-US-JennyNeural", "name": "Jenny (US - Female / Warm)", "lang": "en-US", "gender": "Female", "provider": "edge-tts"},
    {"id": "en-US-AvaNeural", "name": "Ava (US - Female / Studio)", "lang": "en-US", "gender": "Female", "provider": "edge-tts"},
    {"id": "en-US-AndrewNeural", "name": "Andrew (US - Male / Storyteller)", "lang": "en-US", "gender": "Male", "provider": "edge-tts"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (UK - Female / British)", "lang": "en-GB", "gender": "Female", "provider": "edge-tts"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK - Male / Accent)", "lang": "en-GB", "gender": "Male", "provider": "edge-tts"},
    {"id": "en-AU-WilliamNeural", "name": "William (Australia - Male)", "lang": "en-AU", "gender": "Male", "provider": "edge-tts"},

    # Hindi Voices
    {"id": "hi-IN-MadhurNeural", "name": "Madhur (Hindi - Male)", "lang": "hi-IN", "gender": "Male", "provider": "edge-tts"},
    {"id": "hi-IN-SwaraNeural", "name": "Swara (Hindi - Female)", "lang": "hi-IN", "gender": "Female", "provider": "edge-tts"},

    # Bengali Voices
    {"id": "bn-IN-BashkarNeural", "name": "Bashkar (Bengali - Male)", "lang": "bn-IN", "gender": "Male", "provider": "edge-tts"},
    {"id": "bn-IN-TanishaaNeural", "name": "Tanishaa (Bengali - Female)", "lang": "bn-IN", "gender": "Female", "provider": "edge-tts"},

    # Spanish Voices
    {"id": "es-ES-AlvaroNeural", "name": "Alvaro (Spanish - Male)", "lang": "es-ES", "gender": "Male", "provider": "edge-tts"},
    {"id": "es-ES-ElviraNeural", "name": "Elvira (Spanish - Female)", "lang": "es-ES", "gender": "Female", "provider": "edge-tts"},

    # French Voices
    {"id": "fr-FR-HenriNeural", "name": "Henri (French - Male)", "lang": "fr-FR", "gender": "Male", "provider": "edge-tts"},
    {"id": "fr-FR-DeniseNeural", "name": "Denise (French - Female)", "lang": "fr-FR", "gender": "Female", "provider": "edge-tts"},

    # German Voices
    {"id": "de-DE-ConradNeural", "name": "Conrad (German - Male)", "lang": "de-DE", "gender": "Male", "provider": "edge-tts"},
    {"id": "de-DE-KatjaNeural", "name": "Katja (German - Female)", "lang": "de-DE", "gender": "Female", "provider": "edge-tts"},

    # Japanese Voices
    {"id": "ja-JP-KeitaNeural", "name": "Keita (Japanese - Male)", "lang": "ja-JP", "gender": "Male", "provider": "edge-tts"},
    {"id": "ja-JP-NanamiNeural", "name": "Nanami (Japanese - Female)", "lang": "ja-JP", "gender": "Female", "provider": "edge-tts"}
]


def get_available_voices():
    """Returns list of curated AI voices."""
    return AVAILABLE_VOICES


async def generate_speech_edge_tts(text: str, voice: str = "en-US-GuyNeural", rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Generate MP3 audio bytes using Microsoft Edge TTS."""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def generate_speech_gtts(text: str, lang: str = "en") -> bytes:
    """Fallback TTS generator using gTTS."""
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        tts.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


PRONUNCIATION_DICTIONARY = {
    r'\be\.g\.\b': 'for example',
    r'\bi\.e\.\b': 'that is',
    r'\betc\.\b': 'et cetera',
    r'\bvs\.\b': 'versus',
    r'\bAI\b': 'A I',
    r'\bAPI\b': 'A P I',
    r'\bPDF\b': 'P D F',
    r'\bURL\b': 'U R L',
}

def apply_pronunciation_dictionary(text: str) -> str:
    """Applies pronunciation dictionary replacements for abbreviations and acronyms."""
    import re
    for pattern, replacement in PRONUNCIATION_DICTIONARY.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


async def synthesize_text_to_audio(text: str, voice: str = "en-US-GuyNeural", rate: str = "+0%") -> bytes:
    """
    Main entrypoint for text synthesis.
    Tries edge-tts first; falls back to gTTS on exception.
    """
    if not text or not text.strip():
        text = "No text available for conversion."

    text = apply_pronunciation_dictionary(text[:100000])

    try:
        return await generate_speech_edge_tts(text=text, voice=voice, rate=rate)
    except Exception as e:
        print(f"Edge TTS error ({e}), switching to gTTS fallback...")
        lang_code = voice.split("-")[0] if "-" in voice else "en"
        return generate_speech_gtts(text=text, lang=lang_code)

