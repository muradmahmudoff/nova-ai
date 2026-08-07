"""
Nova AI - Plugin Sistemi: Baza İnterfeys
=============================================
Hər plugin bu sinifdən miras alaraq özünü sistemə tanıdır.
LangGraph agent bu pluginləri "tool" (alət) kimi çağıra bilir.

Yeni plugin yazmaq üçün:
    1. app/plugins/builtin/ altında yeni fayl yarat
    2. BasePlugin-dən miras al, name/description/parameters təyin et
    3. execute() metodunu implementasiya et
    4. loader.py avtomatik tapıb yükləyəcək (heç bir əlavə qeydiyyat lazım deyil)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """Bütün pluginlər üçün ümumi interfeys."""

    #: Plugin-in unikal adı (LLM-ə tool kimi göstərilir)
    name: str = "base_plugin"
    #: LLM-in "bu aləti nə vaxt çağırmalı" başa düşməsi üçün təsvir
    description: str = "Təsvir yoxdur"
    #: JSON-Schema formatında parametrlər (OpenAI/Anthropic tool-calling formatına uyğun)
    parameters: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Plugin-in əsas məntiqi. Nəticəni string olaraq qaytarır (LLM-ə geri veriləcək)."""
        raise NotImplementedError

    def to_tool_schema(self) -> dict:
        """LLM provider tool-calling formatına çevirir."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
