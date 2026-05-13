from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import langextract as lx
from langextract import data

from backend.services.pdf_extractor import PDFExtractor


class LangExtractService:
    def __init__(
        self,
        api_key: str | None = None,
        model_id: str = "gemini-2.5-flash",
        max_char_buffer: int = 2000,
        temperature: float = 0,
        extraction_passes: int = 1,
        extract_function: Callable[..., Any] | None = None,
    ):
        self.api_key = api_key
        self.model_id = model_id
        self.max_char_buffer = max_char_buffer
        self.temperature = temperature
        self.extraction_passes = extraction_passes
        self.extract_function = extract_function or lx.extract

    def extract_from_pdf(
        self,
        file_path: str,
        question: str,
        instruction: str,
    ) -> list[dict[str, Any]]:
        pages = PDFExtractor(file_path).extract_pages()
        document_name = Path(file_path).name

        return self.extract_from_pages(
            pages=pages,
            question=question,
            instruction=instruction,
            document_name=document_name,
        )

    def extract_from_pages(
        self,
        pages: list[dict[str, Any]],
        question: str,
        instruction: str,
        document_name: str | None = None,
    ) -> list[dict[str, Any]]:
        documents = [
            data.Document(
                text=str(page["text"]),
                document_id=f"page_{page['page']}",
                additional_context=self._build_page_context(
                    page=int(page["page"]),
                    question=question,
                    document_name=document_name,
                ),
            )
            for page in pages
            if str(page.get("text", "")).strip()
        ]

        return self._extract_documents(
            documents=documents,
            question=question,
            instruction=instruction,
            document_name=document_name,
        )

    def extract_from_text(
        self,
        text: str,
        question: str,
        instruction: str,
        document_name: str | None = None,
    ) -> list[dict[str, Any]]:
        document = data.Document(
            text=text,
            document_id=document_name or "document",
            additional_context=self._build_document_context(
                question=question,
                document_name=document_name,
            ),
        )

        return self._extract_documents(
            documents=[document],
            question=question,
            instruction=instruction,
            document_name=document_name,
        )

    def _extract_documents(
        self,
        documents: list[data.Document],
        question: str,
        instruction: str,
        document_name: str | None,
    ) -> list[dict[str, Any]]:
        if not documents:
            return []

        result = self.extract_function(
            documents,
            prompt_description=self._build_prompt_description(
                question=question,
                instruction=instruction,
            ),
            examples=self._build_examples(),
            model_id=self.model_id,
            api_key=self.api_key,
            max_char_buffer=self.max_char_buffer,
            temperature=self.temperature,
            extraction_passes=self.extraction_passes,
            show_progress=False,
            resolver_params={"suppress_parse_errors": True},
        )

        annotated_documents = (
            result if isinstance(result, list) else [result]
        )

        return self._serialize_extractions(
            annotated_documents=annotated_documents,
            document_name=document_name,
        )

    def _build_prompt_description(self, question: str, instruction: str) -> str:
        return (
            "Extraia somente trechos do documento que ajudem a responder a "
            "pergunta. Não responda, não resuma e não invente dados.\n\n"
            f"Pergunta: {question}\n"
            f"Instrução de extração: {instruction}\n\n"
            "Para cada evidência, use extraction_class='evidencia' e preserve "
            "o texto exatamente como aparece no documento. Quando possível, "
            "adicione atributos como tipo, data, valor, parte, requisito ou "
            "observação."
        )

    def _build_examples(self) -> list[data.ExampleData]:
        return [
            data.ExampleData(
                text=(
                    "O cliente poderá cancelar a reserva até 24 horas antes "
                    "do horário agendado, sem cobrança de multa."
                ),
                extractions=[
                    data.Extraction(
                        extraction_class="evidencia",
                        extraction_text=(
                            "cancelar a reserva até 24 horas antes do horário "
                            "agendado"
                        ),
                        attributes={"tipo": "prazo"},
                    ),
                    data.Extraction(
                        extraction_class="evidencia",
                        extraction_text="sem cobrança de multa",
                        attributes={"tipo": "penalidade"},
                    ),
                ],
            )
        ]

    def _build_page_context(
        self,
        page: int,
        question: str,
        document_name: str | None,
    ) -> str:
        context = self._build_document_context(
            question=question,
            document_name=document_name,
        )
        return f"{context}\nPágina: {page}"

    def _build_document_context(
        self,
        question: str,
        document_name: str | None,
    ) -> str:
        document = document_name or "N/A"
        return f"Documento: {document}\nPergunta do usuário: {question}"

    def _serialize_extractions(
        self,
        annotated_documents: Iterable[data.AnnotatedDocument],
        document_name: str | None,
    ) -> list[dict[str, Any]]:
        serialized = []

        for annotated_document in annotated_documents:
            page = self._parse_page(annotated_document.document_id)

            for extraction in annotated_document.extractions or []:
                serialized.append(
                    {
                        "document": document_name or annotated_document.document_id,
                        "page": page,
                        "class": extraction.extraction_class,
                        "text": extraction.extraction_text,
                        "attributes": extraction.attributes or {},
                        "char_interval": self._serialize_char_interval(
                            extraction.char_interval
                        ),
                    }
                )

        return serialized

    def _parse_page(self, document_id: str | None) -> int | None:
        if not document_id or not document_id.startswith("page_"):
            return None

        try:
            return int(document_id.removeprefix("page_"))
        except ValueError:
            return None

    def _serialize_char_interval(self, char_interval: Any) -> dict[str, int] | None:
        if char_interval is None:
            return None

        if char_interval.start_pos is None or char_interval.end_pos is None:
            return None

        return {
            "start": int(char_interval.start_pos),
            "end": int(char_interval.end_pos),
        }
