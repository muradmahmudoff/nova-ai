"""
Nova AI - Speech-to-Text (faster-whisper)
==============================================
Mikrofondan gələn səsi (numpy array və ya wav fayl) mətnə çevirir.
faster-whisper CTranslate2 üzərində işlədiyi üçün adi Whisper-dən qat-qat
sürətlidir və CPU-da belə real-vaxta yaxın performans verir.

Dəstəklənən dillər: Azərbaycan (az), İngilis (en), Türk (tr) - modelin
`language` parametri boş buraxılsa avtomatik aşkarlayır, sabit versək daha sürətli işləyir.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np

from app.core.exceptions import AudioError
from app.core.logging_config import logger
from config.settings import settings


class SpeechToText:
    """faster-whisper üzərində async wrapper."""

    def __init__(self, model_size: str = "small", device: str = "auto", compute_type: str = "int8"):
        """
        Args:
            model_size: tiny|base|small|medium|large-v3 (böyük model = daha dəqiq, daha yavaş)
            device: 'cpu' | 'cuda' | 'auto'
            compute_type: 'int8' (sürətli, az yaddaş) | 'float16' (GPU üçün) | 'float32'
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise AudioError(
                "faster-whisper quraşdırılmayıb. Səs funksiyaları üçün: "
                "pip install -e '.[audio]'"
            ) from e

        logger.info("Whisper modeli yüklənir: {} ({})", model_size, device)
        self._model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(settings.models_dir / "whisper"),
        )

    async def transcribe_file(self, audio_path: str | Path, language: str | None = None) -> str:
        """Wav/mp3 fayldan mətn çıxarır."""
        return await asyncio.to_thread(self._transcribe_sync, str(audio_path), language)

    async def transcribe_array(self, audio: np.ndarray, language: str | None = None) -> str:
        """Mikrofondan gələn numpy array-dən (16kHz, mono, float32) mətn çıxarır."""
        return await asyncio.to_thread(self._transcribe_sync, audio, language)

    def _transcribe_sync(self, audio, language: str | None) -> str:
        try:
            segments, info = self._model.transcribe(
                audio,
                language=language,  # None -> avtomatik aşkarlama (az/en/tr arasında)
                beam_size=5,
                vad_filter=True,  # səssizlik hissələrini avtomatik ata
            )
            text = " ".join(seg.text.strip() for seg in segments)
            logger.debug("STT nəticəsi (dil={}): {}", info.language, text)
            return text.strip()
        except Exception as e:
            logger.error("STT xətası: {}", e)
            raise AudioError(f"Səs mətnə çevrilə bilmədi: {e}") from e


_stt_instance: SpeechToText | None = None


def get_stt() -> SpeechToText:
    """Singleton instans - model yalnız bir dəfə yaddaşa yüklənir (bahalı əməliyyatdır)."""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance
