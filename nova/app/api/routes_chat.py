"""
Nova AI - Chat REST API
===========================
Mətn əsaslı söhbət və fayl yükləmə endpoint-ləri.
Səsli söhbət üçün routes_ws.py-dəki WebSocket endpoint-inə bax.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.agent.graph import run_agent
from app.core.file_reader import FileReadError, read_any_file
from app.core.logging_config import logger
from app.memory.memory_manager import get_memory_manager

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    response: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Mətn mesajı göndərib Nova-nın cavabını alır."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş ola bilməz")

    memory = get_memory_manager()
    conversation_id = await memory.ensure_conversation(request.conversation_id)

    try:
        response_text = await run_agent(conversation_id, request.message)
    except Exception as e:
        logger.error("Agent icrası uğursuz oldu: {}", e)
        raise HTTPException(status_code=500, detail=f"Daxili xəta: {e}") from e

    return ChatResponse(conversation_id=conversation_id, response=response_text)


@router.post("/upload")
async def upload_file(file: UploadFile) -> dict:
    """PDF/DOCX/TXT/şəkil faylını qəbul edib içindəki mətni (və ya metadata-nı) qaytarır.
    Nəticə sonra əsas /api/chat sorğusunda kontekst kimi istifadə edilə bilər.
    """
    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        extracted = await read_any_file(tmp_path)
    except FileReadError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {"filename": file.filename, "extracted_text": extracted[:5000]}


@router.get("/history/{conversation_id}")
async def get_history(conversation_id: str) -> dict:
    """Bir söhbətin tam tarixçəsini qaytarır (GUI-də göstərmək üçün)."""
    memory = get_memory_manager()
    messages = await memory.get_recent_history(conversation_id, limit=200)
    return {
        "conversation_id": conversation_id,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }
