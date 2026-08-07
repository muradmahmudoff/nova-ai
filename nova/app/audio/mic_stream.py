"""
Nova AI - Mikrofon Axını
============================
sounddevice ilə mikrofondan real-vaxt audio oxuyur və async generator
şəklində ötürür. Wake-word detector və GUI mic düyməsi bunu istifadə edir.
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

import numpy as np

from app.core.logging_config import logger

SAMPLE_RATE = 16000  # Whisper və openWakeWord-un gözlədiyi standart tezlik
CHUNK_SIZE = 1280  # ~80ms @ 16kHz - wake-word modelləri üçün optimal pəncərə


async def microphone_chunks(sample_rate: int = SAMPLE_RATE, chunk_size: int = CHUNK_SIZE) -> AsyncIterator[np.ndarray]:
    """Mikrofondan davamlı olaraq audio parçaları (int16) əldə edən async generator.
    YALNIZ desktop GUI-də istifadə olunur (server/web axınında brauzer özü audio göndərir).
    Bu funksiya çağırılanda sounddevice lazy import edilir.

    İstifadə:
        async for chunk in microphone_chunks():
            ...
    """
    try:
        import sounddevice as sd
    except ImportError as e:
        raise RuntimeError(
            "sounddevice quraşdırılmayıb. Desktop mikrofon üçün: pip install -e '.[gui]'"
        ) from e

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            logger.warning("Mikrofon statusu: {}", status)
        # sounddevice callback ayrı thread-də işləyir, ona görə thread-safe şəkildə queue-ya atırıq
        loop.call_soon_threadsafe(queue.put_nowait, indata.copy().flatten())

    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        blocksize=chunk_size,
        callback=callback,
    )

    with stream:
        logger.info("Mikrofon dinləməsi başladı (sample_rate={})", sample_rate)
        try:
            while True:
                chunk = await queue.get()
                yield chunk
        except asyncio.CancelledError:
            logger.info("Mikrofon dinləməsi dayandırıldı")
            raise


async def record_utterance(
    silence_threshold: float = 500.0,
    silence_duration_s: float = 1.2,
    max_duration_s: float = 15.0,
) -> np.ndarray:
    """İstifadəçi danışığını qeydə alır, o susana qədər davam edir (Voice Activity heuristikası).

    Returns:
        float32 numpy array (Whisper üçün normallaşdırılmış [-1, 1])
    """
    frames: list[np.ndarray] = []
    silence_chunks_needed = int(silence_duration_s * SAMPLE_RATE / CHUNK_SIZE)
    max_chunks = int(max_duration_s * SAMPLE_RATE / CHUNK_SIZE)
    silence_count = 0
    started = False

    async for chunk in microphone_chunks():
        frames.append(chunk)
        volume = float(np.abs(chunk).mean())

        if volume > silence_threshold:
            started = True
            silence_count = 0
        elif started:
            silence_count += 1

        if (started and silence_count >= silence_chunks_needed) or len(frames) >= max_chunks:
            break

    audio = np.concatenate(frames).astype(np.float32) / 32768.0
    return audio
