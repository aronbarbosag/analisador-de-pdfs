import pytest

from backend.services.query_rewriter import QueryRewriter


@pytest.mark.skip(reason="economizar tokens durante desenvolvimento")
def test_gemini_api():
    question = "Até quando posso cancelar minha assinatura?"
    rewriter = QueryRewriter()
    rewriter.rewrite(question)

    response_text = rewriter.response_text
    tokens = rewriter.total_tokens
    print(f"tokens: {tokens}")
    print(response_text)

    assert response_text is not None
    assert len(response_text) > 0
    assert tokens is not None
    assert tokens > 0
