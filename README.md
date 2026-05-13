# Analisador de Documentos PDF com IA

Aplicação em Python para receber um PDF, aceitar uma pergunta em linguagem natural e retornar uma resposta útil no formato JSON obrigatório do desafio técnico:

```json
{
  "type": "text",
  "text": "<resposta em Markdown>",
  "source": "<nome do documento ou N/A>",
  "suggestions": ["<pergunta 1>", "<pergunta 2>", "<pergunta 3>"]
}
```

O fluxo principal usa a API da OpenAI de ponta a ponta. O projeto também mantém um fluxo bônus com Gemini + LangExtract para comparação de qualidade e custo.




<img width="1620" height="788" alt="fluxo-chamadas" src="https://github.com/user-attachments/assets/abbd12b0-9ee5-45d2-8f43-2662d4f3ea22" />



## Sumário

- [Visão geral](#visão-geral)
- [Fluxos disponíveis](#fluxos-disponíveis)
- [Arquitetura](#arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Como executar com Docker](#como-executar-com-docker)
- [Como executar com uv](#como-executar-com-uv)
- [Como executar com pip](#como-executar-com-pip)
- [Como rodar testes](#como-rodar-testes)
- [Estimativa de custo](#estimativa-de-custo)
- [Fluxo visual](#Fluxo-visual)
- [Decisões técnicas](#decisões-técnicas)
- [Conclusão](#Conclusão)


## Imagem da aplicação
<img width="1857" height="987" alt="imagem_do_projeto" src="https://github.com/user-attachments/assets/765f25e9-75b7-4b27-8148-8140c4278597" />


## Visão geral

A aplicação possui uma interface em Streamlit para upload do PDF e envio da pergunta. O backend extrai texto do PDF com PyMuPDF, prepara a pergunta, seleciona trechos relevantes, extrai evidências estruturadas e gera a resposta final validada com Pydantic.
O desafio foi construido com base em princípios de orientação a objetos e o design pattern facade para bibliotecas externas além de ta coberto por testes automatizados

Principais recursos:

- upload de PDF via frontend;
- extração local de texto com `pymupdf`;
- fluxo principal usando OpenAI;
- saída final validada com Pydantic;
- Structured Outputs na OpenAI;
- cálculo de tokens e estimativa de custo em dólar e real;
- fluxo bônus Gemini + LangExtract para benchmark;
- testes unitários e testes de integração opt-in.

## Duas opções de caminho

### 1. Usando OpenAI de ponta a ponta

A ideia não é simplesmente pegar o documento e enviar para IA responder e depois mandar ela formatar a resposta, isso é ineficiente.
Dito isso o fluxo principal pensado foi o seguinte, na verdade o fluxo principal que eu pensei foi o com Gemini por que eu ja conhecia o LangExtract
mas como há a exigencia de usar a OpenAi então ficou dessa maneira abaixo.

```text
PDF upload
-> PDFExtractor local
-> OpenAI reescreve a pergunta
-> seleção local de páginas e chunks relevantes
-> OpenAI extrai evidências estruturadas
-> OpenAI gera resposta final
-> Pydantic valida o JSON final
-> Streamlit exibe resposta, JSON, tokens e custo
```


### 2. Usando Gemini + LangExtract de ponta a ponta

Esse na verdade foi o fluxo pensado primeiro e foi por ele que comecei a elaborar os testes e criar a base da camada de negócio depois foi evoluindo.

```text
PDF upload
-> PDFExtractor local
-> Gemini reescreve a pergunta
-> seleção local de páginas relevantes
-> LangExtract extrai evidências
-> Gemini gera resposta final
-> Pydantic valida o JSON final
-> Streamlit exibe resposta, JSON, tokens e custo
```

## Arquitetura

Componentes principais:
frontend - onde contem a interface que é exposta pro usuário, poderia ser um app desktop, mobile ou outro.
backend - onde está o core da lógica do dominio
tests - onde estão os testes automatizados -> testes de unidade + testes de integração para sustentar longevidade do software e ajudar na identificação de erros  + bugs.

Sobre alguns arquivos e a separação das responsabilidades

- `frontend/app.py`: interface Streamlit.
- `backend/services/pdf_extractor.py`: extração de texto e páginas do PDF.
- `backend/services/document_qa_service.py`: orquestra o fluxo completo.
- `backend/services/openai_agent.py`: cliente OpenAI.
- `backend/services/openai_extraction_service.py`: extração de evidências com OpenAI.
- `backend/services/gemini_agent.py`: cliente Gemini usado no fluxo bônus.
- `backend/services/langextract_service.py`: integração com LangExtract.
- `backend/schemas/`: validações Pydantic e schemas para Structured Outputs.
- `backend/prompts/`: prompts de reescrita, extração e resposta final.

## Estrutura do projeto

```text
.
├── assets/ -> arquivos estáticos utilizados para testes
│   ├── sample.pdf
│   └── sample_2.pdf
├── backend/ -> lógica central
│   ├── prompts/
│   ├── schemas/
│   └── services/
├── frontend/ -> user interface para interação
│   └── app.py -> aqui que executa a aplicação
├── tests/
├── Dockerfile -> arquivo para replicar o projeto num container
├── docker-compose.yml -> aplicação containerizada
├── requirements.txt - > requirements para quem ainda usa pip (ultrapassado já)
├── pyproject.toml - > arquivo de gestão de projetos modernos em Python semelhante ao package-json do Node JS
└── README.md -> esse arquivo aqui com algumas isntruções
```

## Variáveis de ambiente

Crie um arquivo`.env` a partir do exemplo[.example] na raiz do projeto.

```bash
cp .env.example .env
```

Obrigatório somente o OPENAI_API_KEY o restante é para personalização.

```env
OPENAI_API_KEY=sua-api-key-aqui
OPENAI_MODEL=gpt-5.4-nano

GEMINI_API_KEY= sua-api-key-gemini-aqui
LANGEXTRACT_API_KEY= sua-api-key-gemini-aqui
GEMINI_MODEL=gemini-2.5-flash-lite
LANGEXTRACT_MODEL=gemini-2.5-flash-lite
LANGEXTRACT_MAX_CHAR_BUFFER=3000
```

Para executar apenas o fluxo OpenAI, `OPENAI_API_KEY` é suficiente.

### Antes de tudo rode o git clone no repositorio e depois de o cd na pasta do projeto

## OPÇÃO 1  - Como executar com Docker
Requisito: ter o Docker Desktop instalado na maquina e configurado no PATH do sistema

```bash
docker compose up --build
```

Acesse:
OBS: Cheque a porta que esta configurada no arquivo docker-compose.yml  caso de erro provavelmente sua porta está ocupada, mude no arquivo

```text
http://localhost:8502
```

Para parar:

```bash
docker compose down
```

## OPÇÃO 2 - Como executar com uv
Requisito: Ter o gerenciador de pacotes uv instalado e configurado como PATH do sistema

Instale as dependências:

```bash
uv sync
```

Execute o frontend:

```bash
uv run streamlit run frontend/app.py --server.port 8502
```

Acesse:

```text
http://localhost:8502
```

## OPÇÃO 3 - Como executar com pip
Requisito: Ter python3 instalado e configurado no PATH do sistema

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

Instale dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
streamlit run frontend/app.py --server.port 8502
```

## Como rodar testes

Testes padrão, sem chamadas reais às APIs externas:

```bash
uv run pytest  -s -v 
```

Testes de integração com APIs externas:

```bash
RUN_INTEGRATION_TESTS=1 uv run pytest -q
```

**Esses testes exigem chaves válidas no `.env` e podem consumir quota.**



## Estimativa de custo

O frontend mostra:

- tokens de entrada;
- tokens de saída;
- tokens totais;
- custo estimado em USD;
- custo estimado em BRL;
- detalhes por etapa.

Fórmula usada:

```text
(tokens_entrada / 1.000.000 * preço_entrada)
+
(tokens_saida / 1.000.000 * preço_saida)
```

Padronização da conversão dolar para real:

```text
US$ 1 = R$ 5
```

Preços configurados:

- OpenAI `gpt-5.4-mini`: US$ 0.75 input / US$ 4.50 output por 1M tokens.
- Gemini `gemini-2.5-flash-lite`: US$ 0.10 input / US$ 0.40 output por 1M tokens.

## Fluxo visual

```text
[Usuário]
  |
  v
[Streamlit UI]
  | upload PDF + pergunta
  v
[PDFExtractor - PyMuPDF]
  | páginas com texto
  v
[DocumentQAService]
  |
  +--> [OpenAI: reescrita da pergunta]
  |       retorna q, terms, type, extract
  |
  +--> [Seleção local de páginas/chunks]
  |       usa terms para reduzir contexto
  |
  +--> [OpenAI: extração de evidências]
  |       Structured Outputs JSON
  |
  +--> [OpenAI: resposta final]
  |       JSON no formato obrigatório
  |
  v
[Pydantic Validation]
  |
  v
[Streamlit UI]
  | resposta Markdown + JSON + tokens + custo
  v
[Usuário]
```

Fluxo bônus comparativo:

```text
[Streamlit UI]
  |
  v
[PDFExtractor]
  |
  v
[Gemini: reescrita da pergunta]
  |
  v
[LangExtract: evidências]
  |
  v
[Gemini: resposta final]
  |
  v
[Pydantic Validation]
  |
  v
[Streamlit UI]
```

## Decisões técnicas

- A escolha do modelo foi baseada na tabela de preços por modelo | input | output a cada 1kk de tokens, disponível tanto no site da OpenAI Developers como o do Gemini além também de testes feitos e medição na pratica do desempenho
- O fluxo principal usa OpenAI para aderir ao requisito do desafio.
- A extração OpenAI usa Structured Outputs para reduzir respostas fora do formato.
- A resposta final é validada com Pydantic antes de ser exibida.
- A extração de evidências usa chunks ranqueados para reduzir tokens.
- O fluxo Gemini + LangExtract foi mantido como bônus comparativo, pois apresentou bom desempenho em extração.


## Conclusão
 No início dos testes o fluxo Gemini + LangExtract superou consideravelmente o desempenho da OpenAI. Somente após configurar mais alguns parametros e implementar chunks que o desempenho ficou parelho, porém pela facilidade, bom desempenho e gratuidade da api do Gemini,    acredito que ele merece está nesse mini benchmark como curiosidade.

 LangExtract é uma biblioteca que os desenvolvedores Google fizeram que transforma texto nao estruturado em estruturado, facilitando assim a interpretação por outros modelos.
 Conheci essa biblioteca através de uma postagem no linkedin que vi há algum tempo.
