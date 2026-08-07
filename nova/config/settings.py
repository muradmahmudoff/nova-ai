"""
Nova AI - Mərkəzi Konfiqurasiya Modulu
========================================
Bütün layihə üzrə istifadə olunan parametrlər burada bir yerdə saxlanılır.
Pydantic Settings .env faylını avtomatik oxuyur və tip yoxlaması edir.

İstifadə:
    from config.settings import settings
    print(settings.llm_provider)
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Layihənin kök qovluğu (bütün nisbi yollar üçün istinad nöqtəsi)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Tətbiqin bütün konfiqurasiya parametrləri.

    Hər sahə .env faylındakı eyni adlı (böyük hərflərlə) dəyişəndən oxunur.
    Məsələn `llm_provider` sahəsi `.env` faylındakı `LLM_PROVIDER`-dən gəlir.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- LLM Provider ----
    llm_provider: Literal["local", "openai", "anthropic", "gemini", "openrouter"] = "local"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-70b-instruct"

    # ---- Dil ----
    default_language: Literal["az", "en", "tr"] = "az"
    auto_detect_language: bool = True

    # ---- Wake Word ----
    wake_word: str = "nova"
    wake_word_enabled: bool = True

    # ---- Verilənlər bazası / Yaddaş ----
    database_url: str = "sqlite+aiosqlite:///./data/nova.db"
    chroma_persist_dir: str = "./data/chroma"

    # ---- Server ----
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # ---- Log ----
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ---- CORS (Vercel/başqa frontend domenləri üçün) ----
    # Vergüllə ayrılmış siyahı, məsələn: "https://nova.vercel.app,https://nova.app"
    cors_allowed_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    # ---- Sabit yollar (kod daxilində hesablanır, .env-dən gəlmir) ----
    @property
    def data_dir(self) -> Path:
        d = BASE_DIR / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def logs_dir(self) -> Path:
        d = BASE_DIR / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def models_dir(self) -> Path:
        d = BASE_DIR / "models"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def plugins_dir(self) -> Path:
        return BASE_DIR / "app" / "plugins" / "builtin"


# Tətbiq boyu istifadə olunan tək (singleton) konfiqurasiya obyekti
settings = Settings()
