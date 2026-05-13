import json
import os

import pytest

from backend.services.document_qa_service import DocumentQAService
from backend.services.openai_agent import OpenAIAgent
from backend.services.openai_extraction_service import OpenAIExtractionService


class FakeAgent:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.usage_calls = 0

    def generate_response(self, prompt, q=None, response_json_schema=None):
        self.calls.append(
            {
                "prompt": prompt,
                "q": q,
                "response_json_schema": response_json_schema,
            }
        )
        return self.responses.pop(0)

    def get_token_usage(self):
        self.usage_calls += 1
        return {
            "prompt_tokens": self.usage_calls * 10,
            "output_tokens": self.usage_calls,
            "total_tokens": self.usage_calls * 11,
        }


class FakeExtractionService:
    def __init__(self):
        self.calls = []

    def extract_from_pages(self, pages, question, instruction, document_name=None):
        self.calls.append(
            {
                "pages": pages,
                "question": question,
                "instruction": instruction,
                "document_name": document_name,
            }
        )
        return [
            {
                "document": document_name,
                "page": 1,
                "class": "evidencia",
                "text": "O campo suggestions deve ter exatamente 3 perguntas.",
                "attributes": {"tipo": "requisito"},
                "char_interval": None,
            }
        ]


def test_document_qa_service_runs_full_pipeline_with_pages():
    final_answer = {
        "type": "text",
        "text": "## Resposta\nO JSON deve conter 3 sugestões.",
        "source": "sample.pdf",
        "suggestions": ["Qual o modelo?", "Qual o prazo?", "Qual o output?"],
    }
    agent = FakeAgent(
        responses=[
            json.dumps(
                {
                    "q": "formato de resposta obrigatório",
                    "terms": ["json", "suggestions"],
                    "type": "outro",
                    "extract": "Extraia requisitos do formato da resposta.",
                }
            ),
            json.dumps(final_answer),
        ]
    )
    extraction_service = FakeExtractionService()
    service = DocumentQAService(
        agent=agent,
        extraction_service=extraction_service,
    )

    result = service.answer_pages(
        pages=[{"page": 1, "text": "O campo suggestions deve ter exatamente 3."}],
        question="Como deve ser a resposta?",
        document_name="sample.pdf",
    )

    assert {key: result[key] for key in final_answer} == final_answer
    assert result["token_usage"] == {
        "prompt_tokens": 30,
        "output_tokens": 3,
        "thoughts_tokens": 0,
        "total_tokens": 33,
        "estimated_cost_usd": result["token_usage"]["estimated_cost_usd"],
        "estimated_cost_brl": result["token_usage"]["estimated_cost_brl"],
        "pricing": result["token_usage"]["pricing"],
        "steps": [
            {
                "step": "Reescrita da pergunta",
                "prompt_tokens": 10,
                "output_tokens": 1,
                "thoughts_tokens": 0,
                "total_tokens": 11,
            },
            {
                "step": "Resposta final",
                "prompt_tokens": 20,
                "output_tokens": 2,
                "thoughts_tokens": 0,
                "total_tokens": 22,
            },
        ],
    }
    assert agent.calls[0]["q"] is not None
    assert agent.calls[0]["response_json_schema"]["name"] == "query_rewrite"
    assert agent.calls[1]["response_json_schema"]["name"] == "final_answer"
    assert extraction_service.calls[0]["question"] == "formato de resposta obrigatório"
    assert (
        extraction_service.calls[0]["instruction"]
        == "Extraia requisitos do formato da resposta."
    )
    assert "O campo suggestions deve ter exatamente 3 perguntas." in agent.calls[1][
        "prompt"
    ]


def test_document_qa_service_returns_valid_fallback_when_final_answer_is_not_json():
    agent = FakeAgent(
        responses=[
            "{}",
            "Resposta em texto livre",
        ]
    )
    service = DocumentQAService(
        agent=agent,
        extraction_service=FakeExtractionService(),
    )

    result = service.answer_pages(
        pages=[{"page": 1, "text": "Texto"}],
        question="Pergunta?",
        document_name="documento.pdf",
    )

    assert result["type"] == "text"
    assert result["source"] == "documento.pdf"
    assert "não veio em JSON válido" in result["text"]
    assert len(result["suggestions"]) == 3


def test_document_qa_service_filters_pages_by_rewritten_terms_before_extraction():
    final_answer = {
        "type": "text",
        "text": "## Resposta\nA evidência está na página relevante.",
        "source": "sample.pdf",
        "suggestions": ["A?", "B?", "C?"],
    }
    agent = FakeAgent(
        responses=[
            json.dumps(
                {
                    "q": "campo suggestions obrigatório",
                    "terms": ["suggestions"],
                    "type": "outro",
                    "extract": "Extraia evidências sobre suggestions.",
                }
            ),
            json.dumps(final_answer),
        ]
    )
    extraction_service = FakeExtractionService()
    service = DocumentQAService(
        agent=agent,
        extraction_service=extraction_service,
        max_pages_for_extraction=1,
    )

    result = service.answer_pages(
        pages=[
            {"page": 1, "text": "Texto introdutório sem relação."},
            {"page": 2, "text": "O campo suggestions deve ter exatamente 3 perguntas."},
            {"page": 3, "text": "Outro trecho sem relação."},
        ],
        question="Como deve ser a resposta?",
        document_name="sample.pdf",
    )

    assert {key: result[key] for key in final_answer} == final_answer
    assert extraction_service.calls[0]["pages"] == [
        {"page": 2, "text": "O campo suggestions deve ter exatamente 3 perguntas."}
    ]


def test_document_qa_service_returns_valid_fallback_when_schema_is_invalid():
    agent = FakeAgent(
        responses=[
            "{}",
            json.dumps(
                {
                    "type": "text",
                    "text": "Resposta sem sugestões suficientes.",
                    "source": "documento.pdf",
                    "suggestions": ["Uma só"],
                }
            ),
        ]
    )
    service = DocumentQAService(
        agent=agent,
        extraction_service=FakeExtractionService(),
    )

    result = service.answer_pages(
        pages=[{"page": 1, "text": "Texto"}],
        question="Pergunta?",
        document_name="documento.pdf",
    )

    assert result["type"] == "text"
    assert result["source"] == "documento.pdf"
    assert "formato JSON obrigatório" in result["text"]
    assert len(result["suggestions"]) == 3


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1" or not os.getenv("OPENAI_API_KEY"),
    reason="Teste de integração com OpenAI. Use RUN_INTEGRATION_TESTS=1.",
)
def test_document_qa_service_openai_integration_runs_full_sample_pdf_flow():
    agent = OpenAIAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        max_output_tokens=1200,
        response_mime_type="application/json",
    )
    service = DocumentQAService(
        agent=agent,
        extraction_service=OpenAIExtractionService(agent=agent),
    )

    result = service.answer_pdf(
        file_path="assets/sample.pdf",
        question="Qual é o formato JSON obrigatório da resposta?",
    )

    print(result)

    assert result["type"] == "text"
    assert result["source"] == "sample.pdf"
    assert isinstance(result["suggestions"], list)
    assert len(result["suggestions"]) == 3
    assert "json" in result["text"].lower()
