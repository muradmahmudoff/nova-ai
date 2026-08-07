"""Dil aşkarlama modulunun testləri."""
from app.agent.language_detector import detect_language


def test_detects_azerbaijani_by_specific_char():
    text = "Salam, mənim adım Anardır və bu gün necəsən?"
    assert detect_language(text) == "az"


def test_detects_english():
    text = "Hello, how are you doing today? I hope everything is fine."
    assert detect_language(text) == "en"


def test_empty_string_returns_default():
    assert detect_language("") in {"az", "en", "tr"}
