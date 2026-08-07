"""
OpenRouter LLM provayder adapteri.
OpenRouter OpenAI-uyğun (OpenAI-compatible) API təqdim edir, ona görə
mövcud OpenAIProvider-i fərqli base_url ilə yenidən istifadə edirik (DRY prinsipi).
"""
from app.llm.providers.openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    name = "openrouter"

    def __init__(self, api_key: str, model: str):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url="https://openrouter.ai/api/v1",
        )
