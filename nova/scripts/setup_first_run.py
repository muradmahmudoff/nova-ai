"""
İlk quraşdırma köməkçisi: lazımi qovluqları yaradır, .env faylını yoxlayır,
verilənlər bazasını inisializasiya edir.
İstifadə: python scripts/setup_first_run.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    print("Nova AI - İlk quraşdırma başlayır...\n")

    for d in ["data", "logs", "models/whisper", "models/piper", "models/wakeword"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
        print(f"  Qovluq hazır: {d}")

    env_path = ROOT / ".env"
    if not env_path.exists():
        shutil.copy(ROOT / ".env.example", env_path)
        print("\n  .env faylı .env.example-dən yaradıldı")
        print("  Zəhmət olmasa .env faylını açıb lazımi API açarlarını doldur")
    else:
        print("\n  .env artıq mövcuddur")

    import asyncio
    from app.memory.database import init_db

    asyncio.run(init_db())
    print("  Verilənlər bazası hazırlandı")

    print("\nQuraşdırma tamamlandı! Növbəti addımlar:")
    print("  1. .env faylında istədiyin LLM provayderin API açarını doldur")
    print("  2. python scripts/run_server.py  -> backend-i başlat")
    print("  3. python scripts/run_gui.py     -> GUI-ni başlat")


if __name__ == "__main__":
    main()
