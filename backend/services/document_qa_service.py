import json
from pathlib import Path
from typing import Any
import unicodedata

from pydantic import ValidationError

from backend.prompts.question_format import QUERY_MEDIUM_PROMPT
from backend.prompts.response_format import FINAL_ANSWER_PROMPT_COMPACT
from backend.schemas.final_answer import FinalAnswer
from backend.schemas.openai_schema import (
    final_answer_response_schema,
    query_rewrite_response_schema,
)
from backend.services.parser_query_rewriter import parse_rewritten_payload
from backend.services.pdf_extractor import PDFExtractor
from backend.services.token_usage import TokenUsageTracker

QUERY_REWRITE_SCHEMA = query_rewrite_response_schema()
FINAL_ANSWER_SCHEMA = final_answer_response_schema()


class DocumentQAService:
    def __init__(
        self,
        agent: Any,
        extraction_service: Any | None = None,
        langextract_service: Any | None = None,
        question_prompt: str = QUERY_MEDIUM_PROMPT,
        final_answer_prompt: str = FINAL_ANSWER_PROMPT_COMPACT,
        max_pages_for_extraction: int | None = 5,
        token_pricing: dict[str, float] | None = None,
    ):
        self.agent = agent
        self.extraction_service = extraction_service or langextract_service
        self.question_prompt = question_prompt
        self.final_answer_prompt = final_answer_prompt
        self.max_pages_for_extraction = max_pages_for_extraction
        self.token_pricing = token_pricing or {}

        if self.extraction_service is None:
            raise ValueError("DocumentQAService requires an extraction service.")

    def answer_pdf(self, file_path: str, question: str) -> dict[str, Any]:
        pages = PDFExtractor(file_path).extract_pages()
        document_name = Path(file_path).name

        return self.answer_pages(
            pages=pages,
            question=question,
            document_name=document_name,
        )

    def answer_pages(
        self,
        pages: list[dict[str, Any]],
        question: str,
        document_name: str | None = None,
    ) -> dict[str, Any]:
        token_usage = TokenUsageTracker(**self.token_pricing)
        rewritten = self._rewrite_question(question)
        token_usage.capture("Reescrita da pergunta", self.agent)
        extraction_question = rewritten["question"] or question
        instruction = rewritten["instruction"] or extraction_question
        pages_for_extraction = self._select_relevant_pages(
            pages=pages,
            terms=rewritten["terms"],
        )

        extracted_data = self.extraction_service.extract_from_pages(
            pages=pages_for_extraction,
            question=extraction_question,
            instruction=instruction,
            document_name=document_name,
        )
        token_usage.capture("Extração de evidências", self.extraction_service)

        final_prompt = self._build_final_prompt(
            question=question,
            document_name=document_name,
            extracted_data=extracted_data,
        )
        raw_answer = self.agent.generate_response(
            final_prompt,
            response_json_schema=FINAL_ANSWER_SCHEMA,
        )
        token_usage.capture("Resposta final", self.agent)

        answer = self._parse_final_answer(
            raw_answer=raw_answer,
            document_name=document_name,
        )
        answer["token_usage"] = token_usage.summary()

        return answer

    def _rewrite_question(self, question: str) -> dict[str, Any]:
        raw_response = self.agent.generate_response(
            question,
            q=self.question_prompt,
            response_json_schema=QUERY_REWRITE_SCHEMA,
        )

        if not raw_response:
            return {
                "question": question,
                "terms": [],
                "type": "outro",
                "instruction": question,
            }

        parsed = parse_rewritten_payload(raw_response)
        if not parsed["question"]:
            parsed["question"] = question
        if not parsed["instruction"]:
            parsed["instruction"] = parsed["question"]

        return parsed

    def _select_relevant_pages(
        self,
        pages: list[dict[str, Any]],
        terms: list[str],
    ) -> list[dict[str, Any]]:
        if self.max_pages_for_extraction is None:
            return pages

        if self.max_pages_for_extraction <= 0:
            return []

        normalized_terms = [
            self._normalize_text(term) for term in terms if self._normalize_text(term)
        ]

        if not normalized_terms:
            return pages[: self.max_pages_for_extraction]

        scored_pages = []
        for index, page in enumerate(pages):
            text = self._normalize_text(str(page.get("text", "")))
            score = sum(text.count(term) for term in normalized_terms)

            if score > 0:
                scored_pages.append((score, index, page))

        if not scored_pages:
            return pages[: self.max_pages_for_extraction]

        ranked_pages = sorted(scored_pages, key=lambda item: (-item[0], item[1]))
        selected_pages = [
            page for _, _, page in ranked_pages[: self.max_pages_for_extraction]
        ]

        return sorted(selected_pages, key=lambda page: int(page["page"]))

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text.lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _build_final_prompt(
        self,
        question: str,
        document_name: str | None,
        extracted_data: list[dict[str, Any]],
    ) -> str:
        return (
            self.final_answer_prompt.replace("{question}", question)
            .replace("{document_name}", document_name or "N/A")
            .replace(
                "{extracted_data}",
                json.dumps(extracted_data, ensure_ascii=False, indent=2),
            )
            .replace(
                "{langextract_data}",
                json.dumps(extracted_data, ensure_ascii=False, indent=2),
            )
        )

    def _parse_final_answer(
        self,
        raw_answer: str | None,
        document_name: str | None,
    ) -> dict[str, Any]:
        if raw_answer:
            try:
                parsed = json.loads(raw_answer)
            except json.JSONDecodeError:
                return self._build_fallback_answer(
                    document_name=document_name,
                    reason="A resposta final não veio em JSON válido.",
                )

            if isinstance(parsed, dict):
                try:
                    answer = FinalAnswer.model_validate(parsed)
                except ValidationError:
                    return self._build_fallback_answer(
                        document_name=document_name,
                        reason=(
                            "A resposta final não seguiu o formato JSON obrigatório."
                        ),
                    )

                return answer.model_dump()

        return self._build_fallback_answer(
            document_name=document_name,
            reason="Não foi possível gerar uma resposta.",
        )

    def _build_fallback_answer(
        self,
        document_name: str | None,
        reason: str,
    ) -> dict[str, Any]:
        return FinalAnswer(
            type="text",
            text=(
                f"{reason} Tente reformular a pergunta ou verificar se o PDF "
                "contém texto extraível."
            ),
            source=document_name or "N/A",
            suggestions=[
                "Quais são os principais pontos do documento?",
                "Quais informações sustentam essa resposta?",
                "Há alguma evidência relevante no documento?",
            ],
        ).model_dump()
