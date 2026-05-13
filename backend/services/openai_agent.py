from openai import OpenAI

from backend.services.interfaces.agent_interface import AgentInterface


class OpenAIAgent(AgentInterface):
    def __init__(
        self,
        api_key,
        model="gpt-5.4-mini",
        max_output_tokens: int = 800,
        temperature: float | None = None,
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
        return OpenAI(api_key=self.api_key)

    def _build_params(
        self,
        prompt: str,
        response_json_schema: dict | None = None,
    ) -> dict:
        params = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": self.max_output_tokens,
        }

        if self.temperature is not None:
            params["temperature"] = self.temperature

        if response_json_schema:
            params["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": response_json_schema["name"],
                    "schema": response_json_schema["schema"],
                    "strict": response_json_schema.get("strict", True),
                }
            }
        elif self.response_mime_type == "application/json":
            params["text"] = {"format": {"type": "json_object"}}

        return params

    def generate_response(
        self,
        prompt: str,
        q: str | None = None,
        response_json_schema: dict | None = None,
    ) -> str | None:
        contents = q.replace("{question}", prompt) if q else prompt

        response = self.client.responses.create(
            **self._build_params(
                contents,
                response_json_schema=response_json_schema,
            )
        )

        if not response:
            return None

        self.response = response
        return response.output_text

    def count_tokens(self, text: str | None = None):
        if text is None:
            usage = self.get_token_usage()
            return usage["total_tokens"] if usage else None

        response = self.client.responses.input_tokens.count(
            model=self.model, input=text
        )
        return response.input_tokens

    def get_token_usage(self) -> dict[str, int] | None:
        if not self.response or not self.response.usage:
            return None

        usage = self.response.usage

        return {
            "prompt_tokens": usage.input_tokens or 0,
            "output_tokens": usage.output_tokens or 0,
            "total_tokens": usage.total_tokens or 0,
        }
