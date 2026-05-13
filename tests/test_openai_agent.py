import os

from dotenv import load_dotenv

from backend.prompts.answer_format import QUERY_GUIDE_INPUT_SHORT, QUERY_GUIDE_INPUT_FULL
from backend.services.openai_agent import OpenAIAgent
import pytest

load_dotenv()


@pytest.mark.skip(reason="Teste de integração")
def test_openai_agent_and_token_count():

    api_key = os.getenv("OPENAI_API_KEY")
    agent = OpenAIAgent(api_key=api_key)

    question = "Até quando posso cancelar minha assinatura?"

    agent_response = agent.generate_response(
        QUERY_GUIDE_INPUT_SHORT.format(question=question)
    )
    token_count = agent.count_tokens(QUERY_GUIDE_INPUT_SHORT.format(question=question))

    print(f"Agent response: {agent_response}")
    print(f"Token count: {token_count}")

    assert agent_response is not None
    assert len(agent_response) > 0
    assert token_count is not None
    assert token_count > 0
