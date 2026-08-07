"""Anthropic (Claude) LLM provayder adapteri."""
from __future__ import annotations

from typing import AsyncIterator

import anthropic

from app.core.exceptions import LLMProviderError
from app.core.logging_config import logger
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMProviderError("ANTHROPIC_API_KEY təyin edilməyib", provider=self.name)
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    @staticmethod
    def _split_system(messages: list[ChatMessage]) -> tuple[str, list[dict]]:
        """Anthropic API-də system mesajı ayrıca parametrdir, messages array-də deyil."""
        system_parts = [m.content for m in messages if m.role == "system"]
        chat = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        return "\n".join(system_parts), chat

    async def generate(self, messages, *, temperature=0.7, max_tokens=2048) -> LLMResponse:
        system, chat = self._split_system(messages)
        try:
            resp = await self._client.messages.create(
                model=self._model,
                system=system or None,
                messages=chat,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except anthropic.APIError as e:
            logger.error("Anthropic API xətası: {}", e)
            raise LLMProviderError(str(e), provider=self.name) from e

        text = "".join(block.text for block in resp.content if block.type == "text")
        return LLMResponse(
            content=text,
            provider=self.name,
            model=self._model,
            tokens_used=resp.usage.input_tokens + resp.usage.output_tokens,
            finish_reason=resp.stop_reason or "stop",
        )

    async def stream(self, messages, *, temperature=0.7, max_tokens=2048) -> AsyncIterator[str]:
        system, chat = self._split_system(messages)
        try:
            async with self._client.messages.stream(
                model=self._model,
                system=system or None,
                messages=chat,
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.APIError as e:
            logger.error("Anthropic stream xətası: {}", e)
            raise LLMProviderError(str(e), provider=self.name) from e

    async def health_check(self) -> bool:
        try:
            await self._client.messages.create(
                model=self._model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
