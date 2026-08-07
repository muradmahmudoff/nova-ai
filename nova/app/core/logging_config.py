"""
Nova AI - Log Sistemi
========================
Loguru əsasında qurulmuş mərkəzi logging konfiqurasiyası.
Həm konsola, həm də fayla (rotasiya ilə) yazır.

İstifadə:
    from app.core.logging_config import logger
    logger.info("Server başladı")
    logger.error("Xəta baş verdi: {}", err)
"""
import sys

from loguru import logger

from config.settings import settings


def configure_logging() -> None:
    """Logger-i konfiqurasiya edir. Tətbiq başlanğıcında bir dəfə çağırılmalıdır."""
    logger.remove()  # default handler-i sil

    # Konsola rəngli çıxış
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Fayla yazma - hər gün rotasiya, 14 gün saxlanılır
    logger.add(
        settings.logs_dir / "nova_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info("Log sistemi konfiqurasiya edildi (səviyyə={})", settings.log_level)


configure_logging()

__all__ = ["logger"]
