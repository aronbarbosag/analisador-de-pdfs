import os

import pytest
from dotenv import load_dotenv

from backend.prompts.question_format import (
    QUERY_GUIDE_INPUT_FULL,
    QUERY_GUIDE_INPUT_SHORT,
    QUERY_MEDIUM_PROMPT,
)
from backend.services.gemini_agent import GeminiAgent

load_dotenv()

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Teste de integração com Gemini. Use RUN_INTEGRATION_TESTS=1 para executar.",
)


@pytest.mark.skip(
    reason="Teste de integração com Gemini. Use RUN_INTEGRATION_TESTS=1 para executar."
)
def test_gemini_api_with_short_prompt():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(
        api_key=api_key, max_output_tokens=120, response_mime_type="application/json"
    )
    response_text = agent.generate_response(question, q=QUERY_GUIDE_INPUT_SHORT)

    tokens = agent.get_token_usage()
    print(tokens)
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens["total_tokens"] > 0


@pytest.mark.skip(
    reason="Teste de integração com Gemini. Use RUN_INTEGRATION_TESTS=1 para executar."
)
def test_gemini_api_with_medium_prompt():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(
        api_key=api_key, max_output_tokens=120, response_mime_type="application/json"
    )
    response_text = agent.generate_response(question, q=QUERY_MEDIUM_PROMPT)

    tokens = agent.get_token_usage()
    print(tokens)
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens["total_tokens"] > 0


@pytest.mark.skip(
    reason="Teste de integração com Gemini. Use RUN_INTEGRATION_TESTS=1 para executar."
)
def test_gemini_api_with_full_prompt():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(
        api_key=api_key,
        max_output_tokens=120,
        response_mime_type="application/json",
    )
    response_text = agent.generate_response(question, q=QUERY_GUIDE_INPUT_FULL)

    tokens = agent.get_token_usage()
    print(tokens)
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens["total_tokens"] > 0
