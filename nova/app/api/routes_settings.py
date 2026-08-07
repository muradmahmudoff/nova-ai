"""
Nova AI - Parametrlər API
=============================
GUI-dəki Settings menyusunun arxa tərəfi: LLM provayder dəyişmək,
yaddaşı təmizləmək, aktiv konfiqurasiyanı görmək.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.exceptions import ConfigurationError
from app.core.logging_config import logger
from app.llm.factory import switch_provider
from app.memory.vector_store import get_vector_store
from config.settings import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ProviderSwitchRequest(BaseModel):
    provider: str


@router.get("")
async def get_settings() -> dict:
    """Həssas olmayan cari konfiqurasiyanı qaytarır (API açarları gizlədilir)."""
    return {
        "llm_provider": settings.llm_provider,
        "default_language": settings.default_language,
        "auto_detect_language": settings.auto_detect_language,
        "wake_word": settings.wake_word,
        "wake_word_enabled": settings.wake_word_enabled,
        "log_level": settings.log_level,
    }


@router.post("/provider")
async def change_provider(request: ProviderSwitchRequest) -> dict:
    """Aktiv LLM provayderini real-vaxtda dəyişir."""
    try:
        provider = switch_provider(request.provider)
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.info("LLM provayder dəyişdirildi: {}", request.provider)
    return {"status": "ok", "active_provider": provider.name}


@router.post("/memory/clear")
async def clear_memory() -> dict:
    """Bütün semantik (uzunmüddətli) yaddaşı sıfırlayır. Söhbət tarixçəsi (SQLite) toxunulmaz qalır."""
    store = get_vector_store()
    await store.delete_all()
    return {"status": "ok", "message": "Semantik yaddaş təmizləndi"}
