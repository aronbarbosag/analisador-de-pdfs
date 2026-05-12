import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.prompts.answer_format import QUERY_REWRITE_PROMPT

load_dotenv()


class QueryRewriter:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.__response = None
        self.__total_token = None
        self.__response_text = None

    def rewrite(self, question: str) -> None:
        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=QUERY_REWRITE_PROMPT.format(question=question),
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=60,
                response_mime_type="application/json",
            ),
        )

        self.__response = response
        self.__total_token = (
            response.usage_metadata.total_token_count
            if response.usage_metadata
            else None
        )
        self.__response_text = response.text

    @property
    def response_text(self):
        return self.__response_text

    @property
    def total_tokens(self):
        return self.__total_token

    @property
    def response(self):
        return self.__response
