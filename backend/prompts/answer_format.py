QUERY_REWRITE_PROMPT = """
Extraia termos para busca em PDF.

Pergunta:
{question}

Retorne só JSON:
{{"terms":["termo1","termo2","termo3","termo4","termo5","termo6"]}}

Não responda. Use sinônimos formais.
"""
