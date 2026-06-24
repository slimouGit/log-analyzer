from openai import OpenAI

from app.llm.base import LLMClient


class OpenAICompatibleLLMClient(LLMClient):
    """Client for local OpenAI-compatible servers such as Ollama and LM Studio."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned an empty response")
        return content
