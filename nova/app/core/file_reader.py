"""
Nova AI - Fayl Oxuma Modulu
===============================
İstifadəçinin yüklədiyi PDF, DOCX, TXT və şəkil fayllarından mətn/məlumat
çıxarır. Gələcəkdə kamera görüntüsü analizi də eyni "vision" interfeysini
istifadə edəcək (bax: `describe_image`), ona görə arxitektura buna hazır qurulub.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.exceptions import NovaException
from app.core.logging_config import logger


class FileReadError(NovaException):
    def __init__(self, message: str):
        super().__init__(message, code="FILE_READ_ERROR")


async def read_txt(path: str | Path) -> str:
    path = Path(path)
    return await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")


async def read_pdf(path: str | Path) -> str:
    def _sync_read() -> str:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    try:
        return await asyncio.to_thread(_sync_read)
    except Exception as e:
        raise FileReadError(f"PDF oxuna bilmədi: {e}") from e


async def read_docx(path: str | Path) -> str:
    def _sync_read() -> str:
        import docx

        document = docx.Document(str(path))
        paragraphs = [p.text for p in document.paragraphs]
        return "\n".join(paragraphs)

    try:
        return await asyncio.to_thread(_sync_read)
    except Exception as e:
        raise FileReadError(f"DOCX oxuna bilmədi: {e}") from e


async def describe_image(path: str | Path) -> dict:
    """Şəklin əsas metadatasını çıxarır. Real semantic təsviri LLM-in vision
    qabiliyyəti vasitəsilə (əgər aktiv provayder dəstəkləyirsə) API qatında edilir;
    bu funksiya yalnız faylı LLM-ə göndərməzdən əvvəl lokal ilkin emalı təmin edir.

    Gələcəkdə kamera görüntüsü analizi də bu funksiyanı çağıracaq -
    fərq yalnız `path`-in fayldan yoxsa canlı kadrdan gəlməsidir.
    """
    def _sync_inspect() -> dict:
        from PIL import Image

        with Image.open(path) as img:
            return {
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
            }

    try:
        return await asyncio.to_thread(_sync_inspect)
    except Exception as e:
        raise FileReadError(f"Şəkil oxuna bilmədi: {e}") from e


_READERS = {
    ".txt": read_txt,
    ".md": read_txt,
    ".pdf": read_pdf,
    ".docx": read_docx,
}

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


async def read_any_file(path: str | Path) -> str:
    """Fayl uzantısına görə düzgün oxuyucunu seçib mətni qaytarır."""
    path = Path(path)
    ext = path.suffix.lower()

    if ext in _IMAGE_EXTENSIONS:
        meta = await describe_image(path)
        return f"[Şəkil faylı: {meta['format']}, ölçü={meta['size']}, rejim={meta['mode']}]"

    reader = _READERS.get(ext)
    if reader is None:
        raise FileReadError(f"Dəstəklənməyən fayl formatı: {ext}")

    logger.info("Fayl oxunur: {}", path.name)
    return await reader(path)
