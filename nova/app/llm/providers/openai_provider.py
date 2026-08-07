"""OpenAI (GPT) LLM provayder adapteri."""
from __future__ import annotations

from typing import AsyncIterator

import openai

from app.core.exceptions import LLMProviderError
from app.core.logging_config import logger
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        if not api_key:
            raise LLMProviderError("OPENAI_API_KEY təyin edilməyib", provider=self.name)
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    @staticmethod
    def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def generate(self, messages, *, temperature=0.7, max_tokens=2048) -> LLMResponse:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except openai.APIError as e:
            logger.error("OpenAI API xətası: {}", e)
            raise LLMProviderError(str(e), provider=self.name) from e

        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            provider=self.name,
            model=self._model,
            tokens_used=resp.usage.total_tokens if resp.usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, messages, *, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except openai.APIError as e:
            logger.error("OpenAI stream xətası: {}", e)
            raise LLMProviderError(str(e), provider=self.name) from e

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
