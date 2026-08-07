"""
Nova AI - Wake Word Aşkarlama (openWakeWord)
=================================================
Sistemi daim dinləyir, yalnız "Nova" (və ya konfiqurasiya edilmiş başqa söz)
deyildikdə aktivləşir. Tam lokal işləyir, internet lazım deyil.

İstifadə axını:
    1. Mikrofon daimi 16kHz mono axın verir (sounddevice ilə)
    2. Hər ~80ms-lik pəncərə WakeWordDetector-ə ötürülür
    3. Wake word aşkarlansa callback çağırılır -> əsl STT/agent axını başlayır

Qeyd: openWakeWord-un standart modelləri ingilis dilinə uyğunlaşdırılıb.
Xüsusi "Nova" sözü üçün custom model train etmək lazımdır (openWakeWord-un
`train_custom_verifier` alətləri ilə). Bu modul strukturu hazır saxlayır,
custom model faylı `models/wakeword/nova.onnx` yoluna qoyulduqda avtomatik işə düşür.
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

import numpy as np

from app.core.exceptions import AudioError
from app.core.logging_config import logger
from config.settings import settings

WakeWordCallback = Callable[[], Awaitable[None]]


class WakeWordDetector:
    """openWakeWord üzərində real-vaxt wake-word aşkarlama."""

    def __init__(self, threshold: float = 0.5):
        self._threshold = threshold
        self._model = None
        self._running = False

    def _ensure_model_loaded(self):
        if self._model is not None:
            return
        from openwakeword.model import Model

        custom_model_path = settings.models_dir / "wakeword" / f"{settings.wake_word}.onnx"
        if custom_model_path.exists():
            logger.info("Xüsusi wake-word modeli yüklənir: {}", custom_model_path)
            self._model = Model(wakeword_models=[str(custom_model_path)])
        else:
            logger.warning(
                "Xüsusi '{}' modeli tapılmadı, default 'hey_jarvis' modeli test üçün istifadə olunur. "
                "Öz wake-word modelini train edib {} yoluna qoy.",
                settings.wake_word, custom_model_path,
            )
            self._model = Model()  # default daxili modellər

    async def listen(self, audio_stream_generator, on_detected: WakeWordCallback) -> None:
        """
        Args:
            audio_stream_generator: async generator, hər çağırışda np.ndarray (int16, 16kHz) qaytarır
            on_detected: wake word aşkarlandıqda çağırılacaq async funksiya
        """
        self._ensure_model_loaded()
        self._running = True
        logger.info("Wake-word dinləmə başladı ('{}')", settings.wake_word)

        try:
            async for chunk in audio_stream_generator:
                if not self._running:
                    break
                scores = await asyncio.to_thread(self._predict, chunk)
                if any(score > self._threshold for score in scores.values()):
                    logger.info("Wake word aşkarlandı!")
                    await on_detected()
        except Exception as e:
            logger.error("Wake-word dinləmə xətası: {}", e)
            raise AudioError(f"Wake-word dinləmə uğursuz oldu: {e}") from e

    def _predict(self, chunk: np.ndarray) -> dict[str, float]:
        return self._model.predict(chunk)

    def stop(self) -> None:
        self._running = False
        logger.info("Wake-word dinləmə dayandırıldı")


_detector_instance: WakeWordDetector | None = None


def get_wake_word_detector() -> WakeWordDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = WakeWordDetector()
    return _detector_instance
