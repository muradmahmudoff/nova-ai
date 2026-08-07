"""
Nova AI - Yaddaş Meneceri
=============================
Bu modul iki yaddaş qatını birləşdirir:
  1. SQLite  -> Dəqiq, xronoloji söhbət tarixçəsi (kim, nə vaxt, nə dedi)
  2. ChromaDB -> Semantik axtarış (məna baxımından əlaqəli köhnə mesajları tapmaq)

Agent (LangGraph) hər cavab verməzdən əvvəl bu menecerdən "kontekst" alır:
  - son N mesaj (qısa müddətli yaddaş)
  - semantik cəhətdən əlaqəli köhnə mesajlar (uzunmüddətli yaddaş)
"""
from __future__ import annotations

from sqlalchemy import select

from app.core.logging_config import logger
from app.llm.base import ChatMessage
from app.memory.database import get_session
from app.memory.models import Conversation, Message
from app.memory.vector_store import get_vector_store


class MemoryManager:
    """Söhbət tarixçəsi və semantik yaddaşın vahid interfeysi."""

    def __init__(self):
        self._vector_store = get_vector_store()

    # ---------- Yazma ----------

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        language: str = "az",
        provider: str = "",
    ) -> None:
        """Mesajı həm SQLite-a (tarixçə), həm ChromaDB-yə (semantik axtarış üçün) yazır."""
        async with get_session() as session:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                language=language,
                provider=provider,
            )
            session.add(msg)

        # Yalnız mənalı mesajları vektor yaddaşa əlavə et (çox qısa mesajları buraxa bilərik)
        if len(content.strip()) > 3:
            await self._vector_store.add(
                content,
                metadata={"conversation_id": conversation_id, "role": role},
            )

    async def ensure_conversation(self, conversation_id: str | None) -> str:
        """Verilmiş ID mövcud deyilsə, yeni söhbət yaradır. ID-ni qaytarır."""
        async with get_session() as session:
            if conversation_id:
                existing = await session.get(Conversation, conversation_id)
                if existing:
                    return existing.id
            conv = Conversation()
            session.add(conv)
            await session.flush()
            return conv.id

    # ---------- Oxuma ----------

    async def get_recent_history(
        self, conversation_id: str, limit: int = 20
    ) -> list[ChatMessage]:
        """Cari söhbətin son N mesajını xronoloji sırada qaytarır (qısa müddətli yaddaş)."""
        async with get_session() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
        rows = list(reversed(rows))  # xronoloji sıraya çevir
        return [ChatMessage(role=r.role, content=r.content) for r in rows]  # type: ignore[arg-type]

    async def get_relevant_context(self, query: str, top_k: int = 5) -> list[str]:
        """Cari sorğuya semantik cəhətdən əlaqəli köhnə mesajları qaytarır (uzunmüddətli yaddaş)."""
        results = await self._vector_store.search(query, top_k=top_k)
        # Yalnız kifayət qədər relevant olanları saxla (səs-küyü azaltmaq üçün)
        return [r["text"] for r in results if r["relevance"] > 0.3]

    async def build_context_messages(
        self, conversation_id: str, user_query: str
    ) -> list[ChatMessage]:
        """Agent üçün tam kontekst hazırlayır: qısa + uzunmüddətli yaddaşı birləşdirir."""
        recent = await self.get_recent_history(conversation_id)
        relevant = await self.get_relevant_context(user_query)

        messages: list[ChatMessage] = []
        if relevant:
            context_block = "\n".join(f"- {r}" for r in relevant)
            messages.append(
                ChatMessage(
                    role="system",
                    content=(
                        "Aşağıda istifadəçi ilə keçmiş söhbətlərdən mənaca əlaqəli "
                        f"parçalar var, lazım gəldikdə istifadə et:\n{context_block}"
                    ),
                )
            )
        messages.extend(recent)
        return messages


_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
