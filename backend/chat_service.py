import os
import re
from typing import Dict, Any, List


def answer_document_question(query: str, sentences: List[Dict[str, Any]], full_text: str) -> Dict[str, Any]:
    """
    Answers questions strictly based on the uploaded document text.
    Provides page-level citations and explicit "Not found" message if unverified.
    """
    query_clean = query.strip().lower()
    query_keywords = [w for w in re.findall(r'\w+', query_clean) if len(w) > 3]

    if not query_keywords:
        return {
            "answer": "Please enter a specific question about the document.",
            "page_references": [],
            "found_in_doc": False
        }

    # Match sentences by keyword overlap
    matched_items = []
    for s in sentences:
        txt_lower = s["text"].lower()
        score = sum(1 for kw in query_keywords if kw in txt_lower)
        if score > 0:
            matched_items.append({"sentence": s["text"], "page_number": s.get("page_number", 1), "score": score})

    matched_items.sort(key=lambda x: x["score"], reverse=True)

    if not matched_items or matched_items[0]["score"] == 0:
        return {
            "answer": f"Information regarding '{query}' was not found in the uploaded document.",
            "page_references": [],
            "found_in_doc": False
        }

    # Synthesize answer from top 3 matching passages
    top_matches = matched_items[:3]
    pages = sorted(list(dict.fromkeys([m["page_number"] for m in top_matches])))

    passage_text = " ".join([m["sentence"] for m in top_matches])
    page_citations_str = ", ".join([f"Page {p}" for p in pages])

    answer = f"Based on {page_citations_str}: {passage_text}"

    return {
        "answer": answer,
        "page_references": pages,
        "found_in_doc": True
    }
