"""
Nova AI - FastAPI Server Giriş Nöqtəsi
===========================================
İşə salmaq:
    python scripts/run_server.py
    və ya
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_chat import router as chat_router
from app.api.routes_settings import router as settings_router
from app.api.routes_ws import router as ws_router
from app.core.logging_config import logger
from app.memory.database import init_db
from app.plugins.loader import get_plugin_registry
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Server başlayanda/dayananda işə düşən əməliyyatlar."""
    logger.info("Nova AI server başlayır...")
    await init_db()
    registry = get_plugin_registry()
    logger.info("Yüklənmiş pluginlər: {}", [p.name for p in registry.all()])
    yield
    logger.info("Nova AI server dayanır...")


app = FastAPI(
    title="Nova AI",
    description="Şəxsi AI köməkçi - backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# GUI (PySide6/Electron) yerli tətbiqdən sorğu edəcəyi üçün CORS açığıq,
# lakin production-da yalnız lazımi origin-ə məhdudlaşdırmaq tövsiyə olunur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "llm_provider": settings.llm_provider}


# ---- Veb interfeys (statik fayllar) ----
# / ünvanına daxil olan brauzer bu qovluqdakı index.html-i alır.
_WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "static"
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
