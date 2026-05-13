import os

import pytest
from dotenv import load_dotenv

from backend.prompts.answer_format import (
    QUERY_GUIDE_INPUT_FULL,
    QUERY_GUIDE_INPUT_SHORT,
)
from backend.services.gemini_agent import GeminiAgent

load_dotenv()


def test_gemini_api_with_short_prompt():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(api_key=api_key, model="gemini-2.5-flash-lite")
    response_text = agent.generate_response(question, q=QUERY_GUIDE_INPUT_SHORT)

    tokens = agent.count_tokens()
    print(f"tokens: {tokens}")
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens > 0


def test_gemini_api_with_full_prompt():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(api_key=api_key, model="gemini-2.5-flash-lite")
    response_text = agent.generate_response(question, q=QUERY_GUIDE_INPUT_FULL)

    tokens = agent.count_tokens()
    print(f"tokens: {tokens}")
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens > 0


def test_gemini_api_with_short_prompt_new_models():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(api_key=api_key)
    response_text = agent.generate_response(question, q=QUERY_GUIDE_INPUT_SHORT)

    tokens = agent.count_tokens()
    print(f"tokens: {tokens}")
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens > 0


def test_gemini_api_with_full_prompt_new_models():
    question = "Até quando posso cancelar minha assinatura?"
    api_key = os.getenv("GEMINI_API_KEY")
    agent = GeminiAgent(api_key=api_key)
    response_text = agent.generate_response(question, q=QUERY_GUIDE_INPUT_FULL)

    tokens = agent.count_tokens()
    print(f"tokens: {tokens}")
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens > 0
