import json
from typing import Any


def parse_rewritten_query(raw_response: str) -> list[str]:
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        return []

    terms = data.get("terms")

    if not isinstance(terms, list):
        return []

    clean_terms = []

    for term in terms:
        if not isinstance(term, str):
            continue

        term = term.strip().lower()

        if term:
            clean_terms.append(term)

    return clean_terms


def parse_rewritten_payload(raw_response: str) -> dict[str, Any]:
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        return {
            "question": "",
            "terms": [],
            "type": "outro",
            "instruction": "",
        }

    if not isinstance(data, dict):
        return {
            "question": "",
            "terms": [],
            "type": "outro",
            "instruction": "",
        }

    question = data.get("q") or data.get("rewritten_question") or ""
    terms = data.get("terms") or data.get("search_terms") or []
    answer_type = data.get("type") or data.get("expected_answer_type") or "outro"
    instruction = (
        data.get("extract")
        or data.get("extraction_instruction")
        or data.get("langextract_instruction")
        or ""
    )

    clean_terms = []
    if isinstance(terms, list):
        for term in terms:
            if isinstance(term, str) and term.strip():
                clean_terms.append(term.strip().lower())

    return {
        "question": question.strip() if isinstance(question, str) else "",
        "terms": clean_terms,
        "type": answer_type.strip() if isinstance(answer_type, str) else "outro",
        "instruction": instruction.strip() if isinstance(instruction, str) else "",
    }
