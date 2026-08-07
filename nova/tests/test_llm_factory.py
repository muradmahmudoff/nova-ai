"""LLM Factory pattern-inin testləri."""
import pytest

from app.core.exceptions import ConfigurationError, LLMProviderError
from app.llm.factory import get_llm_provider
from config.settings import settings


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "unknown_provider")
    with pytest.raises(ConfigurationError):
        get_llm_provider(force_reload=True)


def test_openai_without_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(LLMProviderError):
        get_llm_provider(force_reload=True)
