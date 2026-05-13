FINAL_ANSWER_PROMPT_COMPACT = """
Responda à pergunta usando somente os dados extraídos do documento.

Pergunta:
{question}

Documento:
{document_name}

Dados extraídos:
{extracted_data}

Retorne somente JSON válido:
{{
  "type": "text",
  "text": "<resposta em Markdown>",
  "source": "<documento ou N/A>",
  "suggestions": ["<pergunta 1>", "<pergunta 2>", "<pergunta 3>"]
}}

Regras:
- Não escreva fora do JSON.
- "type" deve ser "text".
- "text" deve usar Markdown válido.
- "source" deve ser o nome do documento ou "N/A".
- "suggestions" deve ter exatamente 3 perguntas relevantes.
- Não invente dados.
- Se faltar evidência, informe isso no campo "text".
"""


FINAL_ANSWER_PROMPT_FULL = """
Você é um assistente que responde perguntas com base em evidências extraídas de um documento.

Sua tarefa é gerar a resposta final para o usuário usando SOMENTE os dados extraídos do documento.

Pergunta original do usuário:
{question}

Nome do documento analisado:
{document_name}

Dados extraídos:
{extracted_data}

Retorne exclusivamente um JSON válido e parseável neste formato:

{{
  "type": "text",
  "text": "<sua resposta em Markdown>",
  "source": "<nome do documento ou N/A>",
  "suggestions": ["<pergunta 1>", "<pergunta 2>", "<pergunta 3>"]
}}

Regras obrigatórias:
- Não escreva nada fora do JSON.
- Não use markdown fora do campo "text".
- O campo "type" deve ser sempre "text".
- O campo "text" deve conter Markdown válido.
- O campo "text" deve responder diretamente à pergunta do usuário.
- Use títulos, listas e destaques em Markdown quando fizer sentido.
- O campo "source" deve conter o nome do documento analisado.
- Se o nome do documento não estiver disponível, use "N/A".
- O campo "suggestions" deve conter exatamente 3 perguntas de acompanhamento relevantes.
- As sugestões devem estar relacionadas ao documento e à pergunta original.
- Não invente informações que não estejam nos dados extraídos.
- Se os dados extraídos forem insuficientes, diga isso claramente no campo "text".
- Preserve páginas, cláusulas ou evidências quando estiverem disponíveis.
- A resposta final deve ser objetiva, clara e útil.
"""
