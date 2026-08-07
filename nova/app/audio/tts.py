"""
Nova AI - Text-to-Speech (Piper TTS)
=========================================
Mətni təbii insan səsinə çevirir. Piper tam lokal işləyir, sürətlidir
və ONNX modelləri üzərində qurulub (GPU tələb etmir).

Qeyd: Piper-in rəsmi Azərbaycan dili modeli yoxdur (bu yazı tarixinə görə),
ona görə weit strategiyası:
  - EN/TR üçün: Piper-in hazır modelləri (en_US, tr_TR)
  - AZ üçün: TR modelindən istifadə (fonetik cəhətdən ən yaxın) və ya
    istifadəçi öz fine-tune edilmiş AZ modelini `models/piper/az.onnx` yoluna
    qoya bilər - kod avtomatik onu seçəcək.
"""
from __future__ import annotations

import asyncio
import io
import wave
from pathlib import Path

from app.core.exceptions import AudioError
from app.core.logging_config import logger
from config.settings import settings

_LANG_MODEL_MAP = {
    "az": "az.onnx",       # istifadəçinin özəl/fine-tune modeli (əgər varsa)
    "en": "en_US-amy-medium.onnx",
    "tr": "tr_TR-fahrettin-medium.onnx",
}
_FALLBACK_MODEL = "tr_TR-fahrettin-medium.onnx"  # AZ modeli yoxdursa TR-ə keç (fonetik yaxınlıq)


class TextToSpeech:
    """Piper TTS üzərində async wrapper. Modelləri lazy-load edir (yalnız lazım olanda)."""

    def __init__(self):
        self._voices: dict[str, object] = {}  # dil -> yüklənmiş PiperVoice instansı
        self._models_dir = settings.models_dir / "piper"
        self._models_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_model_path(self, language: str) -> Path:
        model_name = _LANG_MODEL_MAP.get(language, _FALLBACK_MODEL)
        path = self._models_dir / model_name
        if not path.exists():
            fallback = self._models_dir / _FALLBACK_MODEL
            if fallback.exists():
                logger.warning("{} modeli tapılmadı, fallback istifadə olunur: {}", language, _FALLBACK_MODEL)
                return fallback
            raise AudioError(
                f"TTS modeli tapılmadı: {path}. "
                f"Zəhmət olmasa Piper modelini models/piper/ qovluğuna endirin "
                f"(bax: https://github.com/rhasspy/piper/blob/master/VOICES.md)"
            )
        return path

    def _load_voice(self, language: str):
        if language in self._voices:
            return self._voices[language]

        from piper import PiperVoice  # lazy import - başlanğıc vaxtını sürətləndirmək üçün

        model_path = self._resolve_model_path(language)
        voice = PiperVoice.load(str(model_path))
        self._voices[language] = voice
        return voice

    async def synthesize(self, text: str, language: str = "az") -> bytes:
        """Mətni WAV formatında audio bayt-larına çevirir."""
        return await asyncio.to_thread(self._synthesize_sync, text, language)

    def _synthesize_sync(self, text: str, language: str) -> bytes:
        try:
            voice = self._load_voice(language)
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                voice.synthesize(text, wav_file)
            return buffer.getvalue()
        except Exception as e:
            logger.error("TTS xətası: {}", e)
            raise AudioError(f"Mətn səsə çevrilə bilmədi: {e}") from e

    async def synthesize_to_file(self, text: str, output_path: str | Path, language: str = "az") -> Path:
        audio_bytes = await self.synthesize(text, language)
        path = Path(output_path)
        path.write_bytes(audio_bytes)
        return path


_tts_instance: TextToSpeech | None = None


def get_tts() -> TextToSpeech:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    return _tts_instance
