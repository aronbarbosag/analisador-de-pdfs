from typing import Any

from google import genai
from google.genai import types

from backend.services.interfaces.agent_interface import AgentInterface


class GeminiAgent(AgentInterface):
    def __init__(
        self,
        api_key,
        model="gemini-2.5-flash-lite",
        max_output_tokens: int = 500,
        temperature: float = 0,
        response_mime_type: str | None = None,
    ):
        self.api_key = api_key
        self.client = self.initialize_client()
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.response_mime_type = response_mime_type
        self.response = None

    def initialize_client(self):
        return genai.Client(api_key=self.api_key)

    def _build_config(self) -> types.GenerateContentConfig:
        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
        }

        if self.response_mime_type:
            config["response_mime_type"] = self.response_mime_type

        return types.GenerateContentConfig(**config)

    def generate_response(
        self,
        prompt: str,
        q: str | None = None,
        **kwargs,
    ) -> str | None:
        # Use replace instead of str.format to avoid interpreting JSON braces
        # inside the prompt template as format placeholders.
        contents = q.replace("{question}", prompt) if q else prompt
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=self._build_config(),
        )
        if not response:
            return None
        self.response = response
        return response.text  # type: ignore

    def count_tokens(self) -> Any:
        if self.response and self.response.usage_metadata:
            return self.response.usage_metadata.total_token_count
        return None

    def get_token_usage(self) -> dict[str, int] | None:
        if not self.response or not self.response.usage_metadata:
            return None

        usage = self.response.usage_metadata

        return {
            "prompt_tokens": usage.prompt_token_count or 0,
            "output_tokens": usage.candidates_token_count or 0,
            "thoughts_tokens": usage.thoughts_token_count or 0,
            "total_tokens": usage.total_token_count or 0,
        }
