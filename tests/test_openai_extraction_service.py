import json
import os

import pytest

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


def test_openai_extraction_service_extracts_page_evidence():
    agent = FakeAgent(
        responses=[
            json.dumps(
                {
                    "extractions": [
                        {
                            "class": "evidencia",
                            "text": "Retorne a resposta OBRIGATORIAMENTE no formato JSON",
                            "attributes": {"tipo": "requisito"},
                        }
                    ]
                }
            )
        ]
    )
    service = OpenAIExtractionService(agent=agent)

    result = service.extract_from_pages(
        pages=[
            {
                "page": 1,
                "text": "Retorne a resposta OBRIGATORIAMENTE no formato JSON.",
            }
        ],
        question="Qual é o formato obrigatório?",
        instruction="Extraia o formato obrigatório.",
        document_name="sample.pdf",
    )

    assert result == [
        {
            "document": "sample.pdf",
            "page": 1,
            "class": "evidencia",
            "text": "Retorne a resposta OBRIGATORIAMENTE no formato JSON",
            "attributes": {"tipo": "requisito"},
            "char_interval": None,
        }
    ]
    assert "Qual é o formato obrigatório?" in agent.calls[0]["prompt"]
    assert "Trecho candidato da página" in agent.calls[0]["prompt"]
    assert agent.calls[0]["response_json_schema"]["name"] == "evidence_extraction"


def test_openai_extraction_service_ignores_invalid_json_and_empty_pages():
    agent = FakeAgent(responses=["não é json"])
    service = OpenAIExtractionService(agent=agent)

    result = service.extract_from_pages(
        pages=[
            {"page": 1, "text": ""},
            {"page": 2, "text": "Texto relevante"},
        ],
        question="Pergunta",
        instruction="Instrução",
        document_name="documento.pdf",
    )

    assert result == []
    assert len(agent.calls) == 1


def test_openai_extraction_service_limits_page_text_sent_to_agent():
    agent = FakeAgent(responses=['{"extractions":[]}'])
    service = OpenAIExtractionService(agent=agent, max_page_chars=10)

    result = service.extract_from_pages(
        pages=[{"page": 1, "text": "1234567890EXTRA"}],
        question="Pergunta",
        instruction="Instrução",
        document_name="documento.pdf",
    )

    assert result == []
    assert "1234567890" in agent.calls[0]["prompt"]
    assert "EXTRA" not in agent.calls[0]["prompt"]


def test_openai_extraction_service_sends_only_top_ranked_chunks():
    agent = FakeAgent(responses=['{"extractions":[]}'])
    service = OpenAIExtractionService(
        agent=agent,
        chunk_chars=20,
        chunk_overlap=0,
        max_chunks=1,
    )

    result = service.extract_from_pages(
        pages=[
            {"page": 1, "text": "texto irrelevante sem termos importantes"},
            {"page": 2, "text": "json obrigatório suggestions resposta final"},
        ],
        question="formato json suggestions",
        instruction="Extraia formato json e suggestions.",
        document_name="sample.pdf",
    )

    assert result == []
    assert len(agent.calls) == 1
    assert "json obrigatório" in agent.calls[0]["prompt"]
    assert "texto irrelevante" not in agent.calls[0]["prompt"]


def test_openai_extraction_service_accumulates_token_usage_across_pages():
    agent = FakeAgent(
        responses=[
            '{"extractions":[]}',
            '{"extractions":[]}',
        ]
    )
    service = OpenAIExtractionService(agent=agent)

    result = service.extract_from_pages(
        pages=[
            {"page": 1, "text": "Texto 1"},
            {"page": 2, "text": "Texto 2"},
        ],
        question="Pergunta",
        instruction="Instrução",
        document_name="documento.pdf",
    )

    assert result == []
    assert service.get_token_usage() == {
        "prompt_tokens": 30,
        "output_tokens": 3,
        "thoughts_tokens": 0,
        "total_tokens": 33,
    }


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1" or not os.getenv("OPENAI_API_KEY"),
    reason="Teste de integração com OpenAI. Use RUN_INTEGRATION_TESTS=1.",
)
def test_openai_extraction_integration_extracts_data_from_sample_pdf():
    agent = OpenAIAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        max_output_tokens=1000,
        response_mime_type="application/json",
    )
    service = OpenAIExtractionService(agent=agent)

    result = service.extract_from_pdf(
        file_path="assets/sample.pdf",
        question="Qual é o formato JSON obrigatório da resposta?",
        instruction="Extraia campos obrigatórios do JSON de resposta.",
    )

    print(result)

    extracted_text = " ".join(item["text"] for item in result).lower()
    assert result
    assert "json" in extracted_text
    assert "suggestions" in extracted_text or "perguntas" in extracted_text
