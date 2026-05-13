from typing import Any


def build_response_json_schema(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "schema": schema,
        "strict": True,
    }


QUERY_REWRITE_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "q": {"type": "string"},
        "terms": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 6,
        },
        "type": {
            "type": "string",
            "enum": [
                "prazo",
                "data",
                "valor",
                "multa",
                "obrigação",
                "cláusula",
                "condição",
                "resumo",
                "outro",
            ],
        },
        "extract": {"type": "string"},
    },
    "required": ["q", "terms", "type", "extract"],
}

EVIDENCE_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "extractions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "class": {"type": "string", "enum": ["evidencia"]},
                    "text": {"type": "string"},
                    "attributes": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "tipo": {"type": "string"},
                        },
                        "required": ["tipo"],
                    },
                },
                "required": ["class", "text", "attributes"],
            },
        }
    },
    "required": ["extractions"],
}

FINAL_ANSWER_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "type": {"type": "string", "enum": ["text"]},
        "text": {"type": "string"},
        "source": {"type": "string"},
        "suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "required": ["type", "text", "source", "suggestions"],
}


def query_rewrite_response_schema() -> dict[str, Any]:
    return build_response_json_schema("query_rewrite", QUERY_REWRITE_JSON_SCHEMA)


def evidence_extraction_response_schema() -> dict[str, Any]:
    return build_response_json_schema(
        "evidence_extraction",
        EVIDENCE_EXTRACTION_JSON_SCHEMA,
    )


def final_answer_response_schema() -> dict[str, Any]:
    return build_response_json_schema("final_answer", FINAL_ANSWER_JSON_SCHEMA)
