import pytest
from pydantic import ValidationError

from backend.schemas.final_answer import FinalAnswer


def test_final_answer_schema_accepts_required_response_format():
    answer = FinalAnswer.model_validate(
        {
            "type": "text",
            "text": "## Resposta\nConteúdo em Markdown.",
            "source": "sample.pdf",
            "suggestions": ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"],
        }
    )

    assert answer.model_dump() == {
        "type": "text",
        "text": "## Resposta\nConteúdo em Markdown.",
        "source": "sample.pdf",
        "suggestions": ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {
            "type": "json",
            "text": "Resposta",
            "source": "sample.pdf",
            "suggestions": ["A?", "B?", "C?"],
        },
        {
            "type": "text",
            "text": "Resposta",
            "source": "sample.pdf",
            "suggestions": ["A?", "B?"],
        },
        {
            "type": "text",
            "text": "Resposta",
            "source": "sample.pdf",
            "suggestions": ["A?", "B?", "C?"],
            "extra": "not allowed",
        },
    ],
)
def test_final_answer_schema_rejects_invalid_response_format(payload):
    with pytest.raises(ValidationError):
        FinalAnswer.model_validate(payload)
