import json


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
