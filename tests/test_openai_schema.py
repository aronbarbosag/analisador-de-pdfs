from backend.schemas.openai_schema import (
    evidence_extraction_response_schema,
    final_answer_response_schema,
    query_rewrite_response_schema,
)


def test_evidence_extraction_schema_is_strict_for_openai_structured_outputs():
    schema = evidence_extraction_response_schema()["schema"]
    extraction_item = schema["properties"]["extractions"]["items"]

    assert schema["required"] == ["extractions"]
    assert extraction_item["additionalProperties"] is False
    assert extraction_item["required"] == ["class", "text", "attributes"]
    assert set(extraction_item["properties"]) == {"class", "text", "attributes"}
    assert extraction_item["properties"]["attributes"]["required"] == ["tipo"]
    assert extraction_item["properties"]["attributes"]["additionalProperties"] is False


def test_query_rewrite_schema_requires_all_properties():
    schema = query_rewrite_response_schema()["schema"]

    assert schema["required"] == ["q", "terms", "type", "extract"]
    assert set(schema["properties"]) == {"q", "terms", "type", "extract"}


def test_final_answer_schema_requires_compact_response_format():
    schema = final_answer_response_schema()["schema"]

    assert schema["required"] == ["type", "text", "source", "suggestions"]
    assert schema["properties"]["type"]["enum"] == ["text"]
    assert schema["properties"]["suggestions"]["minItems"] == 3
    assert schema["properties"]["suggestions"]["maxItems"] == 3
