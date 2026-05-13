import os
from types import SimpleNamespace

import pytest
from dotenv import load_dotenv

from backend.prompts.question_format import (
    QUERY_GUIDE_INPUT_SHORT,
)
from backend.schemas.openai_schema import final_answer_response_schema
from backend.services.openai_agent import OpenAIAgent

load_dotenv()


class FakeResponses:
    def __init__(self):
        self.create_params = None
        self.input_tokens = SimpleNamespace(
            count=lambda model, input: SimpleNamespace(input_tokens=42)
        )

    def create(self, **kwargs):
        self.create_params = kwargs
        return SimpleNamespace(
            output_text='{"ok": true}',
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=5,
                total_tokens=15,
            ),
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


class FakeOpenAIAgent(OpenAIAgent):
    def initialize_client(self):
        return FakeClient()


def test_openai_agent_generates_response_with_template_and_json_config():
    agent = FakeOpenAIAgent(
        api_key="test",
        model="gpt-test",
        max_output_tokens=123,
        temperature=0,
        response_mime_type="application/json",
    )

    response = agent.generate_response("Pergunta?", q="Responda: {question}")

    assert response == '{"ok": true}'
    assert agent.client.responses.create_params == {
        "model": "gpt-test",
        "input": "Responda: Pergunta?",
        "max_output_tokens": 123,
        "temperature": 0,
        "text": {"format": {"type": "json_object"}},
    }
    assert agent.get_token_usage() == {
        "prompt_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
    assert agent.count_tokens() == 15
    assert agent.count_tokens("abc") == 42


def test_openai_agent_accepts_structured_output_schema_override():
    agent = FakeOpenAIAgent(
        api_key="test",
        model="gpt-test",
        max_output_tokens=123,
        response_mime_type="application/json",
    )
    schema = final_answer_response_schema()

    response = agent.generate_response("Pergunta?", response_json_schema=schema)

    assert response == '{"ok": true}'
    assert agent.client.responses.create_params["text"]["format"]["type"] == (
        "json_schema"
    )
    assert agent.client.responses.create_params["text"]["format"]["name"] == (
        "final_answer"
    )
    assert agent.client.responses.create_params["text"]["format"]["strict"] is True
    assert "properties" in agent.client.responses.create_params["text"]["format"][
        "schema"
    ]


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Teste de integração com OpenAI. Use RUN_INTEGRATION_TESTS=1 para executar.",
)
def test_openai_agent_and_token_count():

    api_key = os.getenv("OPENAI_API_KEY")
    agent = OpenAIAgent(
        api_key=api_key,
        max_output_tokens=120,
        response_mime_type="application/json",
    )

    question = "Até quando posso cancelar minha assinatura?"

    agent_response = agent.generate_response(question, q=QUERY_GUIDE_INPUT_SHORT)
    token_count = agent.count_tokens(QUERY_GUIDE_INPUT_SHORT.format(question=question))

    print(f"Agent response: {agent_response}")
    print(f"Token count: {token_count}")

    assert agent_response is not None
    assert len(agent_response) > 0
    assert token_count is not None
    assert token_count > 0
