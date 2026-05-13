QUERY_GUIDE_INPUT_SHORT = """
Extraia termos para busca em PDF.

Pergunta:
{question}

Retorne só JSON:
{{"terms":["termo1","termo2","termo3","termo4","termo5","termo6"]}}

Não responda. Use sinônimos formais.
"""

QUERY_GUIDE_INPUT_FULL = """
Você é um módulo de preparação de perguntas para extração de informações em PDFs.

Sua tarefa NÃO é responder à pergunta.

Sua tarefa é transformar a pergunta do usuário em uma estrutura curta e útil para:
1. buscar trechos relevantes no PDF;
2. orientar a extração estruturada sobre o que deve ser extraído.

Pergunta do usuário:
{question}

Retorne somente JSON válido no formato abaixo:

{{
  "rewritten_question": "pergunta reescrita de forma objetiva",
  "search_terms": [
    "termo1",
    "termo2",
    "termo3",
    "termo4",
    "termo5",
    "termo6"
  ],
  "expected_answer_type": "prazo | data | valor | cláusula | obrigação | penalidade | condição | parte | resumo | outro",
  "extraction_instruction": "instrução curta e direta sobre o que deve ser extraído dos trechos encontrados"
}}

Regras:
- Não responda à pergunta.
- Não invente dados.
- Preserve exatamente a intenção da pergunta original.
- Use termos formais que possam aparecer em contratos, políticas, editais ou documentos oficiais.
- Inclua sinônimos úteis nos search_terms.
- Use no máximo 6 termos em search_terms.
- A extraction_instruction deve ter no máximo 25 palavras.
- Não use markdown.
- Não escreva nada fora do JSON.
"""


QUERY_MEDIUM_PROMPT = """
Prepare a pergunta para busca em PDF e extração estruturada de evidências.

Pergunta:
{question}

Retorne somente JSON válido:
{{
  "q": "pergunta reescrita de forma objetiva",
  "terms": ["termo1","termo2","termo3","termo4","termo5","termo6"],
  "type": "prazo | data | valor | multa | obrigação | cláusula | condição | resumo | outro",
  "extract": "instrução curta para extração estruturada"
}}

Regras:
- Não responda à pergunta.
- Não invente dados.
- Use termos formais comuns em contratos e documentos.
- terms deve ter no máximo 6 itens.
- extract deve ter no máximo 20 palavras.
- Não use markdown.
"""
