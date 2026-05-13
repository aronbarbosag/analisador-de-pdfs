from openai import OpenAI

from backend.services.interfaces.agent_interface import AgentInterface


class OpenAIAgent(AgentInterface):
    def __init__(self, api_key, model="gpt-5.2"):
        self.api_key = api_key
        self.client = self.initialize_client()
        self.model = model

    def initialize_client(self):
        return OpenAI(api_key=self.api_key)

    def generate_response(self, prompt):

        response = self.client.responses.create(model=self.model, input=prompt)

        return response.output_text

    def count_tokens(self, text):
        response = self.client.responses.input_tokens.count(
            model=self.model, input=text
        )
        return response.input_tokens
