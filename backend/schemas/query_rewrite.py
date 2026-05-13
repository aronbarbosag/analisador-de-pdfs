from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryRewrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str = Field(min_length=1)
    terms: list[str] = Field(max_length=6)
    type: Literal[
        "prazo",
        "data",
        "valor",
        "multa",
        "obrigação",
        "cláusula",
        "condição",
        "resumo",
        "outro",
    ]
    extract: str = Field(min_length=1, max_length=160)

    @field_validator("q", "extract")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be empty")
        return value

    @field_validator("terms")
    @classmethod
    def clean_terms(cls, terms: list[str]) -> list[str]:
        clean_terms = []
        for term in terms:
            term = term.strip().lower()
            if term:
                clean_terms.append(term)
        return clean_terms
