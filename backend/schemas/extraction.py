from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_: Literal["evidencia"] = Field(alias="class")
    text: str = Field(min_length=1)
    attributes: dict[str, str]

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be empty")
        return value


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extractions: list[EvidenceExtraction]
