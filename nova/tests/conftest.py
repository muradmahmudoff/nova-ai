"""Pytest üçün ümumi fixture-lar."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch, tmp_path):
    """Hər testi müvəqqəti qovluqda, real .env-dən asılı olmadan işlədir."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    yield
