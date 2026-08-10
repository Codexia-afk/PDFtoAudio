import uuid
import re
from typing import Dict, Any, List


def generate_flashcards(sentences: List[Dict[str, Any]], count: int = 8) -> List[Dict[str, Any]]:
    """Generates flashcards with front/back concepts and page references."""
    flashcards = []
    candidates = [s for s in sentences if 30 < len(s["text"]) < 180]

    for i, s in enumerate(candidates[:count], start=1):
        txt = s["text"]
        page_num = s.get("page_number", 1)

        # Split sentence into question concept (Front) and answer detail (Back)
        parts = re.split(r'\b(is|are|means|refers to|shows|indicates|contains|includes)\b', txt, maxsplit=1, flags=re.I)
        if len(parts) >= 3:
            front = f"What {parts[1].lower()} {parts[0].strip()}?"
            back = parts[2].strip()
        else:
            front = f"Explain concept from Page {page_num}: '{txt[:40]}...'"
            back = txt

        flashcards.append({
            "id": str(uuid.uuid4()),
            "front": front.capitalize(),
            "back": back.capitalize(),
            "page_reference": page_num,
            "difficulty": "medium" if i % 2 == 0 else "easy"
        })

    return flashcards


def generate_quiz_questions(sentences: List[Dict[str, Any]], count: int = 5) -> List[Dict[str, Any]]:
    """Generates multiple-choice quiz questions with explanations and page references."""
    quizzes = []
    candidates = [s for s in sentences if 30 < len(s["text"]) < 160]

    for i, s in enumerate(candidates[:count], start=1):
        txt = s["text"]
        page_num = s.get("page_number", 1)
        words = [w for w in txt.split() if len(w) > 4]

        correct_word = words[0] if words else "Concept"
        alt1 = "Unrelated Theory"
        alt2 = "Alternative Hypothesis"
        alt3 = "General Standard"

        options = [correct_word, alt1, alt2, alt3]
        # Shuffle deterministically
        options = [options[(j + i) % 4] for j in range(4)]
        correct_idx = options.index(correct_word)

        question_text = txt.replace(correct_word, "_______", 1)

        quizzes.append({
            "id": str(uuid.uuid4()),
            "question": f"Fill in the blank (Page {page_num}): {question_text}",
            "options": options,
            "correct_option_index": correct_idx,
            "explanation": f"According to Page {page_num}, the correct term is '{correct_word}'. Full passage: '{txt}'",
            "page_reference": page_num
        })

    return quizzes


def export_flashcards_anki_csv(flashcards: List[Dict[str, Any]]) -> str:
    """Exports flashcards in Anki-compatible CSV format."""
    lines = ["#separator:Comma", "#html:true", "Front,Back,PageReference"]
    for fc in flashcards:
        front = fc['front'].replace('"', '""')
        back = fc['back'].replace('"', '""')
        page = fc['page_reference']
        lines.append(f'"{front}","{back}","Page {page}"')
    return "\n".join(lines)
