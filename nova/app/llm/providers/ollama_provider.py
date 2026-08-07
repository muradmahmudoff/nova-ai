"""
Ollama (lokal model) LLM provayder adapteri.
İnternetsiz, tam lokal işləmək istəyənlər üçün. Ollama öz OpenAI-uyğun
endpoint-ini /v1 altında verir, ona görə yenə OpenAIProvider-dən miras alırıq.
API açarı tələb olunmur (dummy dəyər veririk, çünki OpenAI SDK boş string qəbul etmir).
"""
from app.llm.providers.openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    name = "local"

    def __init__(self, base_url: str, model: str):
        super().__init__(
            api_key="ollama-local",  # Ollama bunu yoxlamır, sadəcə SDK tələb edir
            model=model,
            base_url=f"{base_url.rstrip('/')}/v1",
        )
