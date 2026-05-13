from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FinalAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"]
    text: str = Field(min_length=1)
    source: str = Field(min_length=1)
    suggestions: list[str] = Field(min_length=3, max_length=3)

    @field_validator("text", "source")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be empty")
        return value

    @field_validator("suggestions")
    @classmethod
    def strip_suggestions(cls, suggestions: list[str]) -> list[str]:
        clean_suggestions = []

        for suggestion in suggestions:
            suggestion = suggestion.strip()
            if not suggestion:
                raise ValueError("suggestions must not contain empty values")
            clean_suggestions.append(suggestion)

        return clean_suggestions
