"""
Nova AI - Verilənlər Bazası Bağlantı İdarəetməsi
=====================================================
Async SQLAlchemy engine və session yaradılması. FastAPI dependency
injection ilə hər sorğuda təmiz bir session verir.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging_config import logger
from app.memory.models import Base
from config.settings import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Tətbiq başlanğıcında cədvəlləri yaradır (əgər yoxdursa)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Verilənlər bazası hazırdır: {}", settings.database_url)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager kimi session verir, avtomatik commit/rollback edir.

    İstifadə:
        async with get_session() as session:
            session.add(obj)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
