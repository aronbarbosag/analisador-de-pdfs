from typing import Any

from google import genai
from google.genai import types

from backend.services.interfaces.agent_interface import AgentInterface


class GeminiAgent(AgentInterface):
    def __init__(self, api_key, model="gemini-3.1-flash-lite"):
        self.api_key = api_key
        self.client = self.initialize_client()
        self.model = model
        self.response = None

    def initialize_client(self):
        return genai.Client(api_key=self.api_key)

    def generate_response(self, prompt: str, q: str) -> None:
        # Use replace instead of str.format to avoid interpreting JSON braces
        # inside the prompt template as format placeholders.
        contents = q.replace("{question}", prompt)
        response = self.client.models.generate_content(
            model=self.model, contents=contents
        )
        if not response:
            return None
        self.response = response
        return response.text  # type: ignore

    def count_tokens(self) -> Any:
        if self.response and self.response.usage_metadata:
            return self.response.usage_metadata.total_token_count
        return None
