import json
from pathlib import Path
from typing import Any
import unicodedata

from pydantic import ValidationError

from backend.prompts.extraction_format import OPENAI_EXTRACTION_PROMPT
from backend.schemas.extraction import ExtractionResult
from backend.schemas.openai_schema import evidence_extraction_response_schema
from backend.services.pdf_extractor import PDFExtractor

EXTRACTION_SCHEMA = evidence_extraction_response_schema()


class OpenAIExtractionService:
    def __init__(
        self,
        agent: Any,
        extraction_prompt: str = OPENAI_EXTRACTION_PROMPT,
        max_page_chars: int = 6000,
        chunk_chars: int = 1400,
        chunk_overlap: int = 180,
        max_chunks: int = 4,
    ):
        self.agent = agent
        self.extraction_prompt = extraction_prompt
        self.max_page_chars = max_page_chars
        self.chunk_chars = chunk_chars
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks
        self.token_usage = None

    def extract_from_pdf(
        self,
        file_path: str,
        question: str,
        instruction: str,
    ) -> list[dict[str, Any]]:
        pages = PDFExtractor(file_path).extract_pages()
        return self.extract_from_pages(
            pages=pages,
            question=question,
            instruction=instruction,
            document_name=Path(file_path).name,
        )

    def extract_from_pages(
        self,
        pages: list[dict[str, Any]],
        question: str,
        instruction: str,
        document_name: str | None = None,
    ) -> list[dict[str, Any]]:
        extractions = []
        self.token_usage = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "thoughts_tokens": 0,
            "total_tokens": 0,
        }

        chunks = self._select_relevant_chunks(
            pages=pages,
            question=question,
            instruction=instruction,
        )

        for chunk in chunks:
            raw_response = self.agent.generate_response(
                self._build_prompt(
                    page=chunk["page"],
                    page_text=chunk["text"],
                    question=question,
                    instruction=instruction,
                    document_name=document_name,
                ),
                response_json_schema=EXTRACTION_SCHEMA,
            )
            self._accumulate_token_usage()

            extractions.extend(
                self._parse_page_extractions(
                    raw_response=raw_response,
                    page=chunk["page"],
                    document_name=document_name,
                )
            )

        return extractions

    def get_token_usage(self) -> dict[str, int] | None:
        return self.token_usage

    def _select_relevant_chunks(
        self,
        pages: list[dict[str, Any]],
        question: str,
        instruction: str,
    ) -> list[dict[str, Any]]:
        query_terms = self._extract_terms(f"{question} {instruction}")
        chunks = []

        for page in pages:
            page_text = self._truncate_page_text(str(page.get("text", "")).strip())
            if not page_text:
                continue

            for chunk_index, chunk_text in enumerate(self._chunk_text(page_text)):
                score = self._score_text(chunk_text, query_terms)
                chunks.append(
                    {
                        "page": int(page["page"]),
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "score": score,
                    }
                )

        if not chunks:
            return []

        ranked_chunks = sorted(
            chunks,
            key=lambda chunk: (-chunk["score"], chunk["page"], chunk["chunk_index"]),
        )
        selected_chunks = ranked_chunks[: self.max_chunks]

        return sorted(
            selected_chunks,
            key=lambda chunk: (chunk["page"], chunk["chunk_index"]),
        )

    def _chunk_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_chars:
            return [text]

        chunks = []
        start = 0
        step = max(self.chunk_chars - self.chunk_overlap, 1)

        while start < len(text):
            chunk = text[start : start + self.chunk_chars].strip()
            if chunk:
                chunks.append(chunk)
            start += step

        return chunks

    def _extract_terms(self, text: str) -> list[str]:
        stopwords = {
            "a",
            "as",
            "o",
            "os",
            "de",
            "do",
            "da",
            "das",
            "dos",
            "e",
            "em",
            "para",
            "por",
            "com",
            "qual",
            "quais",
            "que",
            "sobre",
            "extraia",
            "evidencias",
            "evidencia",
        }
        normalized_text = self._normalize_text(text)
        terms = []

        for raw_term in normalized_text.replace("?", " ").replace(".", " ").split():
            term = raw_term.strip(",;:()[]{}")
            if len(term) < 4 or term in stopwords:
                continue
            terms.append(term)

        return list(dict.fromkeys(terms))

    def _score_text(self, text: str, terms: list[str]) -> int:
        normalized_text = self._normalize_text(text)
        score = sum(normalized_text.count(term) for term in terms)
        return score

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text.lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _accumulate_token_usage(self) -> None:
        get_token_usage = getattr(self.agent, "get_token_usage", None)
        if not callable(get_token_usage) or self.token_usage is None:
            return

        usage = get_token_usage()
        if not usage:
            return

        for key in self.token_usage:
            value = usage.get(key, 0)
            self.token_usage[key] += value if isinstance(value, int) else 0

    def _build_prompt(
        self,
        page: int,
        page_text: str,
        question: str,
        instruction: str,
        document_name: str | None,
    ) -> str:
        return (
            self.extraction_prompt.replace("{document_name}", document_name or "N/A")
            .replace("{page}", str(page))
            .replace("{question}", question)
            .replace("{instruction}", instruction)
            .replace("{page_text}", page_text)
        )

    def _truncate_page_text(self, page_text: str) -> str:
        if len(page_text) <= self.max_page_chars:
            return page_text

        return page_text[: self.max_page_chars]

    def _parse_page_extractions(
        self,
        raw_response: str | None,
        page: int,
        document_name: str | None,
    ) -> list[dict[str, Any]]:
        if not raw_response:
            return []

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            return []

        try:
            extraction_result = ExtractionResult.model_validate(parsed)
        except ValidationError:
            return []

        extractions = []
        for extraction in extraction_result.extractions:
            extractions.append(
                {
                    "document": document_name or "N/A",
                    "page": page,
                    "class": extraction.class_,
                    "text": extraction.text,
                    "attributes": extraction.attributes,
                    "char_interval": None,
                }
            )

        return extractions
