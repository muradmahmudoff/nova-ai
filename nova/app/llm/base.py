"""
Nova AI - LLM Provider Abstract Interface
=============================================
Bütün LLM provayderləri (OpenAI, Anthropic, Gemini, OpenRouter, Ollama/local)
bu abstrakt sinfi implementasiya edir. Bu sayədə tətbiqin qalan hissəsi hansı
provayderin işlədiyindən asılı olmadan eyni interfeyslə işləyir (Strategy Pattern).

Yeni provayder əlavə etmək üçün:
    1. BaseLLMProvider-dən miras al
    2. generate() və stream() metodlarını implementasiya et
    3. factory.py-də registry-yə əlavə et
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    """Tək bir söhbət mesajı."""
    role: Role
    content: str


@dataclass
class LLMResponse:
    """Provayderdən qayıdan cavab, metadata ilə birlikdə."""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    extra: dict = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Bütün LLM provayderləri üçün ümumi interfeys."""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Tam cavabı bir dəfəyə qaytarır (streaming olmadan)."""
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Cavabı token-token axın (stream) şəklində qaytarır.
        Səsli danışıq zamanı TTS-ə real-vaxt ötürmək üçün vacibdir.
        """
        raise NotImplementedError

    async def health_check(self) -> bool:
        """Provayderin əlçatan olub-olmadığını yoxlayır. Alt-siniflər override edə bilər."""
        return True
