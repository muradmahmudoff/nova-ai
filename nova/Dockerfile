# Nova AI - Backend server üçün Docker image
# Qeyd: GUI (PySide6) konteynerdə işləmir, yalnız backend (FastAPI) konteynerləşdirilir.
# GUI-ni host maşınında lokal işlətmək lazımdır.

FROM python:3.11-slim

# Audio kitabxanaları (faster-whisper, piper) üçün lazımi sistem paketləri
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /nova

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip

COPY . .
# BAŞLANĞIC üçün yalnız əsas (core) asılılıqlar quraşdırılır - mətn chat, yaddaş,
# fayl oxuma işləyir. Bu, build-in mütləq uğurlu olmasını təmin edir.
#
# Səs funksiyalarını (STT/TTS/wake-word) aktivləşdirmək istəsən, aşağıdakı sətri
#   RUN pip install --no-cache-dir -e .
# bununla əvəz et:
#   RUN pip install --no-cache-dir -e ".[audio]"
# (diqqət: bu, build vaxtını və image ölçüsünü xeyli artırır)
#
# 'gui' qrupu (PySide6, sounddevice) BURAYA HEÇ VAXT ƏLAVƏ EDİLMİR - server-də
# lazım deyil, headless mühitdə işləmir və build-i sındırır.
RUN pip install --no-cache-dir -e .

RUN mkdir -p data logs models/whisper models/piper models/wakeword

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "scripts/run_server.py"]
