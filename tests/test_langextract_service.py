import os

import pytest
from langextract import data

from backend.services.pdf_extractor import PDFExtractor
from backend.services.langextract_service import LangExtractService


def test_extract_from_pages_calls_langextract_and_preserves_page_metadata():
    captured = {}

    def fake_extract(documents, **kwargs):
        captured["documents"] = documents
        captured["kwargs"] = kwargs

        return [
            data.AnnotatedDocument(
                document_id="page_2",
                extractions=[
                    data.Extraction(
                        extraction_class="evidencia",
                        extraction_text="Sistema disponível 24 horas",
                        char_interval=data.CharInterval(start_pos=10, end_pos=38),
                        attributes={"tipo": "requisito"},
                    )
                ],
            )
        ]

    service = LangExtractService(
        api_key="test-key",
        model_id="gemini-test",
        max_char_buffer=1234,
        extract_function=fake_extract,
    )

    result = service.extract_from_pages(
        pages=[
            {"page": 1, "text": " "},
            {"page": 2, "text": "Sistema disponível 24 horas para reservas."},
        ],
        question="O sistema fica disponível quando?",
        instruction="Extraia a disponibilidade do sistema.",
        document_name="sample_2.pdf",
    )

    assert [document.document_id for document in captured["documents"]] == ["page_2"]
    assert captured["documents"][0].additional_context.endswith("Página: 2")
    assert "O sistema fica disponível quando?" in captured["kwargs"][
        "prompt_description"
    ]
    assert "Extraia a disponibilidade do sistema." in captured["kwargs"][
        "prompt_description"
    ]
    assert captured["kwargs"]["api_key"] == "test-key"
    assert captured["kwargs"]["model_id"] == "gemini-test"
    assert captured["kwargs"]["max_char_buffer"] == 1234
    assert captured["kwargs"]["show_progress"] is False
    assert len(captured["kwargs"]["examples"]) == 1
    assert result == [
        {
            "document": "sample_2.pdf",
            "page": 2,
            "class": "evidencia",
            "text": "Sistema disponível 24 horas",
            "attributes": {"tipo": "requisito"},
            "char_interval": {"start": 10, "end": 38},
        }
    ]


def test_extract_from_text_accepts_single_annotated_document_result():
    def fake_extract(documents, **kwargs):
        return data.AnnotatedDocument(
            document_id="desafio.pdf",
            extractions=[
                data.Extraction(
                    extraction_class="evidencia",
                    extraction_text="Retorne a resposta OBRIGATORIAMENTE",
                )
            ],
        )

    service = LangExtractService(extract_function=fake_extract)

    result = service.extract_from_text(
        text="Retorne a resposta OBRIGATORIAMENTE no formato JSON.",
        question="Qual é o formato obrigatório?",
        instruction="Extraia o formato obrigatório da resposta.",
        document_name="desafio.pdf",
    )

    assert result == [
        {
            "document": "desafio.pdf",
            "page": None,
            "class": "evidencia",
            "text": "Retorne a resposta OBRIGATORIAMENTE",
            "attributes": {},
            "char_interval": None,
        }
    ]


def test_extract_from_pdf_uses_assets_pdf_text_and_root_output_reference():
    expected_excerpt = "DESAFIO TÉCNICO"
    pdf_text = PDFExtractor("assets/sample.pdf").extract_text()
    captured = {}

    def fake_extract(documents, **kwargs):
        captured["documents"] = documents
        return []

    service = LangExtractService(extract_function=fake_extract)

    result = service.extract_from_pdf(
        file_path="assets/sample.pdf",
        question="Qual é o objetivo do desafio?",
        instruction="Extraia objetivo e requisitos obrigatórios.",
    )

    assert expected_excerpt in pdf_text
    assert any(expected_excerpt in document.text for document in captured["documents"])
    assert captured["documents"][0].document_id.startswith("page_")
    assert result == []


def test_extract_from_empty_pages_returns_empty_list_without_calling_langextract():
    def fake_extract(documents, **kwargs):
        raise AssertionError("LangExtract should not run without document text")

    service = LangExtractService(extract_function=fake_extract)

    result = service.extract_from_pages(
        pages=[{"page": 1, "text": ""}],
        question="Pergunta",
        instruction="Instrução",
    )

    assert result == []


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1"
    or not (os.getenv("LANGEXTRACT_API_KEY") or os.getenv("GEMINI_API_KEY")),
    reason=(
        "Teste de integração com LangExtract. Use RUN_INTEGRATION_TESTS=1 "
        "e configure LANGEXTRACT_API_KEY ou GEMINI_API_KEY."
    ),
)
def test_langextract_integration_extracts_relevant_data_from_sample_pdf():
    api_key = os.getenv("LANGEXTRACT_API_KEY") or os.getenv("GEMINI_API_KEY")
    service = LangExtractService(
        api_key=api_key,
        model_id=os.getenv("LANGEXTRACT_MODEL", "gemini-2.5-flash-lite"),
        max_char_buffer=3000,
    )

    result = service.extract_from_pdf(
        file_path="assets/sample.pdf",
        question="Qual é o formato JSON obrigatório da resposta?",
        instruction=(
            "Extraia os campos obrigatórios do JSON de resposta e regras sobre "
            "source, text e suggestions."
        ),
    )

    extracted_text = " ".join(item["text"] for item in result).lower()

    print(result)

    assert result
    assert any(item["page"] is not None for item in result)
    assert "json" in extracted_text
    assert "suggestions" in extracted_text or "perguntas" in extracted_text


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1"
    or not (os.getenv("LANGEXTRACT_API_KEY") or os.getenv("GEMINI_API_KEY")),
    reason=(
        "Teste de integração com LangExtract. Use RUN_INTEGRATION_TESTS=1 "
        "e configure LANGEXTRACT_API_KEY ou GEMINI_API_KEY."
    ),
)
def test_langextract_integration_extracts_relevant_data_from_sample_2_pdf():
    api_key = os.getenv("LANGEXTRACT_API_KEY") or os.getenv("GEMINI_API_KEY")
    service = LangExtractService(
        api_key=api_key,
        model_id=os.getenv("LANGEXTRACT_MODEL", "gemini-2.5-flash-lite"),
        max_char_buffer=3000,
    )

    result = service.extract_from_pdf(
        file_path="assets/sample_2.pdf",
        question="Quais são os requisitos funcionais do cliente?",
        instruction="Extraia requisitos funcionais associados ao ator Cliente.",
    )

    extracted_text = " ".join(item["text"] for item in result).lower()

    print(result)

    assert result
    assert any(item["document"] == "sample_2.pdf" for item in result)
    assert "cliente" in extracted_text
    assert "reserva" in extracted_text or "login" in extracted_text
