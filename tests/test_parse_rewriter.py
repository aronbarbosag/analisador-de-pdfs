from backend.services.parser_query_rewriter import (
    parse_rewritten_payload,
    parse_rewritten_query,
)


def test_parse_rewritten_query_valid_json():
    raw_response = '{"terms":["cancelamento","assinatura","prazo","rescisão"]}'

    result = parse_rewritten_query(raw_response)

    assert result == ["cancelamento", "assinatura", "prazo", "rescisão"]


def test_parse_rewritten_query_removes_empty_terms():
    raw_response = '{"terms":["cancelamento","","  ","prazo"]}'

    result = parse_rewritten_query(raw_response)

    assert result == ["cancelamento", "prazo"]


def test_parse_rewritten_query_returns_empty_list_when_invalid_json():
    raw_response = "termos: cancelamento, assinatura, prazo"

    result = parse_rewritten_query(raw_response)

    assert result == []


def test_parse_rewritten_query_returns_empty_list_when_terms_missing():
    raw_response = '{"query":"cancelamento assinatura prazo"}'

    result = parse_rewritten_query(raw_response)

    assert result == []


def test_parse_rewritten_payload_supports_medium_prompt_shape():
    raw_response = """
    {
      "q": "prazo para cancelar assinatura",
      "terms": ["Cancelamento", "  prazo  "],
      "type": "prazo",
      "extract": "Extraia o prazo de cancelamento."
    }
    """

    result = parse_rewritten_payload(raw_response)

    assert result == {
        "question": "prazo para cancelar assinatura",
        "terms": ["cancelamento", "prazo"],
        "type": "prazo",
        "instruction": "Extraia o prazo de cancelamento.",
    }


def test_parse_rewritten_payload_supports_full_prompt_shape():
    raw_response = """
    {
      "rewritten_question": "valor da multa",
      "search_terms": ["Multa", "Penalidade"],
      "expected_answer_type": "penalidade",
      "langextract_instruction": "Extraia multas e penalidades."
    }
    """

    result = parse_rewritten_payload(raw_response)

    assert result == {
        "question": "valor da multa",
        "terms": ["multa", "penalidade"],
        "type": "penalidade",
        "instruction": "Extraia multas e penalidades.",
    }


def test_parse_rewritten_payload_supports_neutral_extraction_instruction():
    raw_response = """
    {
      "rewritten_question": "valor da multa",
      "search_terms": ["Multa"],
      "expected_answer_type": "multa",
      "extraction_instruction": "Extraia o valor da multa."
    }
    """

    result = parse_rewritten_payload(raw_response)

    assert result == {
        "question": "valor da multa",
        "terms": ["multa"],
        "type": "multa",
        "instruction": "Extraia o valor da multa.",
    }
