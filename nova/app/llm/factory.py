"""
Nova AI - LLM Provider Factory
==================================
Factory Pattern: config.settings.llm_provider dəyərinə əsasən düzgün
provayder instansını yaradır. Tətbiqin qalan hissəsi yalnız bu funksiyanı
çağırır, hansı provayderin arxada işlədiyini bilmək məcburiyyətində deyil.

İstifadə:
    from app.llm.factory import get_llm_provider
    provider = get_llm_provider()
    response = await provider.generate([...])
"""
from __future__ import annotations

from app.core.exceptions import ConfigurationError
from app.core.logging_config import logger
from app.llm.base import BaseLLMProvider
from config.settings import settings

_provider_instance: BaseLLMProvider | None = None


def get_llm_provider(force_reload: bool = False) -> BaseLLMProvider:
    """Aktiv konfiqurasiyaya uyğun LLM provayder instansını qaytarır (singleton).

    Args:
        force_reload: True olduqda, mövcud instansdan asılı olmayaraq yenidən yaradır
                       (məsələn, istifadəçi Settings menyusundan provayderi dəyişdikdə).
    """
    global _provider_instance

    if _provider_instance is not None and not force_reload:
        return _provider_instance

    provider_name = settings.llm_provider
    logger.info("LLM provayder yüklənir: {}", provider_name)

    if provider_name == "openai":
        from app.llm.providers.openai_provider import OpenAIProvider
        _provider_instance = OpenAIProvider(settings.openai_api_key, settings.openai_model)

    elif provider_name == "anthropic":
        from app.llm.providers.anthropic_provider import AnthropicProvider
        _provider_instance = AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)

    elif provider_name == "gemini":
        from app.llm.providers.gemini_provider import GeminiProvider
        _provider_instance = GeminiProvider(settings.gemini_api_key, settings.gemini_model)

    elif provider_name == "openrouter":
        from app.llm.providers.openrouter_provider import OpenRouterProvider
        _provider_instance = OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_model)

    elif provider_name == "local":
        from app.llm.providers.ollama_provider import OllamaProvider
        _provider_instance = OllamaProvider(settings.ollama_base_url, settings.ollama_model)

    else:
        raise ConfigurationError(f"Naməlum LLM provayder: {provider_name}")

    return _provider_instance


def switch_provider(new_provider: str) -> BaseLLMProvider:
    """İşləyən tətbiqdə real-vaxtda provayder dəyişmək üçün (Settings menyusundan çağırılır)."""
    valid = {"local", "openai", "anthropic", "gemini", "openrouter"}
    if new_provider not in valid:
        raise ConfigurationError(f"Naməlum provayder: {new_provider}. Mümkün: {valid}")
    settings.llm_provider = new_provider  # type: ignore[assignment]
    return get_llm_provider(force_reload=True)
