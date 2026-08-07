"""
Nova AI - Agent State
=========================
LangGraph qrafının addımları arasında daşınan vəziyyət (state).
Hər node (addım) bu obyekti oxuyur/yeniləyir.
"""
from __future__ import annotations

from typing import TypedDict

from app.llm.base import ChatMessage


class AgentState(TypedDict, total=False):
    """Agent qrafının hər node-u arasında paylaşılan state."""

    conversation_id: str
    user_input: str
    detected_language: str
    context_messages: list[ChatMessage]
    tool_calls: list[dict]
    tool_results: list[str]
    final_response: str
    error: str | None
