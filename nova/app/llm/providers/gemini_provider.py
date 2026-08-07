"""Google Gemini LLM provayder adapteri."""
from __future__ import annotations

from typing import AsyncIterator

import google.generativeai as genai

from app.core.exceptions import LLMProviderError
from app.core.logging_config import logger
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMProviderError("GEMINI_API_KEY təyin edilməyib", provider=self.name)
        genai.configure(api_key=api_key)
        self._model_name = model
        self._model = genai.GenerativeModel(model)

    @staticmethod
    def _to_gemini_history(messages: list[ChatMessage]) -> tuple[str | None, list[dict]]:
        system = next((m.content for m in messages if m.role == "system"), None)
        history = []
        for m in messages:
            if m.role == "system":
                continue
            role = "model" if m.role == "assistant" else "user"
            history.append({"role": role, "parts": [m.content]})
        return system, history

    async def generate(self, messages, *, temperature=0.7, max_tokens=2048) -> LLMResponse:
        system, history = self._to_gemini_history(messages)
        model = genai.GenerativeModel(self._model_name, system_instruction=system)
        try:
            resp = await model.generate_content_async(
                history,
                generation_config=genai.GenerationConfig(
                    temperature=temperature, max_output_tokens=max_tokens
                ),
            )
        except Exception as e:
            logger.error("Gemini API xətası: {}", e)
            raise LLMProviderError(str(e), provider=self.name) from e

        return LLMResponse(
            content=resp.text,
            provider=self.name,
            model=self._model_name,
            tokens_used=getattr(resp.usage_metadata, "total_token_count", 0) or 0,
        )

    async def stream(self, messages, *, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        system, history = self._to_gemini_history(messages)
        model = genai.GenerativeModel(self._model_name, system_instruction=system)
        try:
            resp = await model.generate_content_async(
                history,
                generation_config=genai.GenerationConfig(
                    temperature=temperature, max_output_tokens=max_tokens
                ),
                stream=True,
            )
            async for chunk in resp:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Gemini stream xətası: {}", e)
            raise LLMProviderError(str(e), provider=self.name) from e
