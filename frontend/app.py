import os
import sys
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.document_qa_service import DocumentQAService  # noqa: E402
from backend.services.gemini_agent import GeminiAgent  # noqa: E402
from backend.services.langextract_service import LangExtractService  # noqa: E402
from backend.services.openai_extraction_service import (  # noqa: E402
    OpenAIExtractionService,
)
from backend.services.openai_agent import OpenAIAgent  # noqa: E402
from backend.services.token_usage import (  # noqa: E402
    gemini_2_5_flash_lite_pricing,
    openai_gpt_5_4_mini_pricing,
)


load_dotenv()


class AppConfigError(ValueError):
    pass


def build_openai_agent(max_output_tokens: int = 1200) -> OpenAIAgent:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AppConfigError("Configure OPENAI_API_KEY no arquivo .env.")

    return OpenAIAgent(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        max_output_tokens=max_output_tokens,
        response_mime_type="application/json",
    )


def build_gemini_agent() -> GeminiAgent:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AppConfigError("Configure GEMINI_API_KEY no arquivo .env.")

    return GeminiAgent(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        max_output_tokens=1200,
        response_mime_type="application/json",
    )


def build_openai_service() -> DocumentQAService:
    agent = build_openai_agent(max_output_tokens=1400)
    extraction_service = OpenAIExtractionService(agent=agent)

    return DocumentQAService(
        agent=agent,
        extraction_service=extraction_service,
        token_pricing=openai_gpt_5_4_mini_pricing(),
    )


def build_bonus_service() -> DocumentQAService:
    langextract_api_key = os.getenv("LANGEXTRACT_API_KEY") or os.getenv(
        "GEMINI_API_KEY"
    )
    if not langextract_api_key:
        raise AppConfigError(
            "Configure LANGEXTRACT_API_KEY ou GEMINI_API_KEY no arquivo .env."
        )

    langextract_service = LangExtractService(
        api_key=langextract_api_key,
        model_id=os.getenv("LANGEXTRACT_MODEL", "gemini-2.5-flash-lite"),
        max_char_buffer=int(os.getenv("LANGEXTRACT_MAX_CHAR_BUFFER", "3000")),
    )

    return DocumentQAService(
        agent=build_gemini_agent(),
        extraction_service=langextract_service,
        token_pricing=gemini_2_5_flash_lite_pricing(),
    )


def save_uploaded_pdf(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return temp_file.name


st.set_page_config(page_title="Analisador de PDFs", layout="centered")

st.title("Analisador de PDFs")

flow = st.selectbox(
    "Fluxo",
    [
        "OpenAI completo (recomendado)",
        "Gemini + LangExtract (bônus comparativo)",
    ],
)
uploaded_pdf = st.file_uploader("PDF", type=["pdf"])
question = st.text_area("Pergunta", placeholder="Digite sua pergunta sobre o PDF")

if st.button("Analisar", type="primary", disabled=not uploaded_pdf or not question):
    temp_path = save_uploaded_pdf(uploaded_pdf)

    try:
        with st.spinner("Extraindo o PDF e buscando evidências..."):
            service = (
                build_bonus_service()
                if flow == "Gemini + LangExtract (bônus comparativo)"
                else build_openai_service()
            )
            answer = service.answer_pdf(temp_path, question)

        st.markdown(answer["text"])

        token_usage = answer.get("token_usage")
        if token_usage:
            st.divider()
            st.caption("Uso de tokens")
            col1, col2, col3 = st.columns(3)
            col1.metric("Entrada", token_usage.get("prompt_tokens", 0))
            col2.metric("Saída", token_usage.get("output_tokens", 0))
            col3.metric("Total", token_usage.get("total_tokens", 0))

            cost1, cost2 = st.columns(2)
            cost1.metric(
                "Estimativa USD",
                f"$ {token_usage.get('estimated_cost_usd', 0):.6f}",
            )
            cost2.metric(
                "Estimativa BRL",
                f"R$ {token_usage.get('estimated_cost_brl', 0):.6f}",
            )
            st.caption(
                "Estimativa: (tokens de entrada / 1.000.000 * preço de entrada) + "
                "(tokens de saída / 1.000.000 * preço de saída), considerando "
                "US$ 1 = R$ 5."
            )

            with st.expander("Detalhes por etapa"):
                st.dataframe(token_usage.get("steps", []), width="stretch")

        st.divider()
        st.caption("JSON de resposta")
        st.json(answer)

        if answer.get("suggestions"):
            st.caption("Sugestões")
            for suggestion in answer["suggestions"]:
                st.write(f"- {suggestion}")

    except AppConfigError as exc:
        st.warning(str(exc))
    except TimeoutError:
        st.error("A chamada demorou demais. Tente novamente com um PDF menor.")
    except Exception as exc:
        st.error(f"Não foi possível processar o PDF: {exc}")
    finally:
        Path(temp_path).unlink(missing_ok=True)

with st.sidebar:
    st.subheader("Configuração")
    st.caption("Fluxo principal")
    st.write(f"OpenAI: `{os.getenv('OPENAI_MODEL', 'gpt-5.4-mini')}`")
    st.caption("Bônus comparativo")
    st.write(f"Gemini: `{os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')}`")
    st.write(
        f"LangExtract: `{os.getenv('LANGEXTRACT_MODEL', 'gemini-2.5-flash-lite')}`"
    )
