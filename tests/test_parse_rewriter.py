from backend.services.parser_query_rewriter import parse_rewritten_query


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
