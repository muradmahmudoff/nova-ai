"""
Nova AI - Real-Vaxt Səsli Söhbət (WebSocket)
=================================================
GUI mikrofon düyməsindən gələn audio bu kanal vasitəsilə server-ə axır,
STT -> Agent -> TTS zənciri işlədikdən sonra audio cavab geri göndərilir.

Protokol (JSON mesajlar):
  Client -> Server:
    {"type": "audio_chunk", "data": "<base64 pcm16>"}
    {"type": "audio_end"}
    {"type": "text_message", "text": "..."}
  Server -> Client:
    {"type": "transcript", "text": "..."}          # STT nəticəsi
    {"type": "response_text", "text": "..."}        # Agent cavabı (mətn)
    {"type": "response_audio", "data": "<base64 wav>"}  # Agent cavabı (səs)
    {"type": "error", "message": "..."}
"""
from __future__ import annotations

import base64
import json

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.graph import run_agent
from app.audio.stt import get_stt
from app.audio.tts import get_tts
from app.core.logging_config import logger
from app.memory.memory_manager import get_memory_manager

router = APIRouter()


@router.websocket("/ws/voice")
async def voice_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("WebSocket səs sessiyası açıldı")

    memory = get_memory_manager()
    conversation_id = await memory.ensure_conversation(None)
    audio_buffer: list[np.ndarray] = []

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            msg_type = message.get("type")

            if msg_type == "audio_chunk":
                pcm_bytes = base64.b64decode(message["data"])
                chunk = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                audio_buffer.append(chunk)

            elif msg_type == "audio_end":
                if not audio_buffer:
                    await websocket.send_json({"type": "error", "message": "Audio boşdur"})
                    continue

                full_audio = np.concatenate(audio_buffer)
                audio_buffer.clear()

                # 1. STT
                stt = get_stt()
                transcript = await stt.transcribe_array(full_audio)
                await websocket.send_json({"type": "transcript", "text": transcript})

                if not transcript.strip():
                    await websocket.send_json({"type": "error", "message": "Heç nə eşidilmədi"})
                    continue

                # 2. Agent
                response_text = await run_agent(conversation_id, transcript)
                await websocket.send_json({"type": "response_text", "text": response_text})

                # 3. TTS
                tts = get_tts()
                audio_bytes = await tts.synthesize(response_text)
                await websocket.send_json({
                    "type": "response_audio",
                    "data": base64.b64encode(audio_bytes).decode("utf-8"),
                })

            elif msg_type == "text_message":
                text = message.get("text", "")
                response_text = await run_agent(conversation_id, text)
                await websocket.send_json({"type": "response_text", "text": response_text})

                tts = get_tts()
                audio_bytes = await tts.synthesize(response_text)
                await websocket.send_json({
                    "type": "response_audio",
                    "data": base64.b64encode(audio_bytes).decode("utf-8"),
                })

            else:
                await websocket.send_json({"type": "error", "message": f"Naməlum mesaj tipi: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("WebSocket səs sessiyası bağlandı")
    except Exception as e:
        logger.error("WebSocket xətası: {}", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
