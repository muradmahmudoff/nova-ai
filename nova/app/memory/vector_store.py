"""
Nova AI - Semantik Vektor Yaddaşı (ChromaDB)
=================================================
Köhnə söhbətlərdən "məna baxımından" (semantic) əlaqəli parçaları tapmaq üçün.
Məsələn istifadəçi "mənim Python layihəm haqqında" desə, sistem tarixçədə
Python sözü keçməsə belə, məna baxımından bağlı mesajları tapa bilir.

Qeyd: ChromaDB sync API-yə malikdir, ona görə asyncio.to_thread ilə
event loop-u bloklamadan çağırırıq.
"""
from __future__ import annotations

import asyncio
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.exceptions import MemoryError_
from app.core.logging_config import logger
from config.settings import settings


class VectorMemoryStore:
    """ChromaDB üzərində semantik yaddaş üçün wrapper."""

    def __init__(self):
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="nova_memory",
            metadata={"hnsw:space": "cosine"},
        )

    async def add(self, text: str, metadata: dict | None = None) -> str:
        """Yeni bir xatirəni (mesaj, fakt və s.) vektor yaddaşa əlavə edir."""
        doc_id = str(uuid.uuid4())
        try:
            await asyncio.to_thread(
                self._collection.add,
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
        except Exception as e:
            logger.error("ChromaDB yazma xətası: {}", e)
            raise MemoryError_(f"Vektor yaddaşa yazıla bilmədi: {e}") from e
        return doc_id

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Sorğuya semantik olaraq ən yaxın xatirələri qaytarır."""
        try:
            result = await asyncio.to_thread(
                self._collection.query,
                query_texts=[query],
                n_results=top_k,
            )
        except Exception as e:
            logger.error("ChromaDB axtarış xətası: {}", e)
            raise MemoryError_(f"Vektor yaddaşda axtarış uğursuz oldu: {e}") from e

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            {"text": d, "metadata": m, "relevance": 1 - dist}
            for d, m, dist in zip(docs, metas, distances)
        ]

    async def delete_all(self) -> None:
        """Bütün semantik yaddaşı təmizləyir (Settings menyusundan 'yaddaşı sıfırla')."""
        await asyncio.to_thread(self._client.delete_collection, "nova_memory")
        self._collection = await asyncio.to_thread(
            self._client.get_or_create_collection,
            name="nova_memory",
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("Vektor yaddaş tamamilə təmizləndi")


_vector_store: VectorMemoryStore | None = None


def get_vector_store() -> VectorMemoryStore:
    """Singleton instans qaytarır."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorMemoryStore()
    return _vector_store
