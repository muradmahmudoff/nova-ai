"""
Nova AI - Parametrlər Dialoqu
=================================
LLM provayder seçimi, dil, wake-word aktivliyi kimi parametrləri
dəyişmək üçün istifadəçi interfeysi.
"""
from __future__ import annotations

import httpx
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

API_BASE = "http://127.0.0.1:8000"


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova - Parametrlər")
        self.setMinimumWidth(360)
        self._build_ui()
        self._load_current_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["local", "openai", "anthropic", "gemini", "openrouter"])
        form.addRow("LLM Provayder:", self._provider_combo)

        self._language_combo = QComboBox()
        self._language_combo.addItems(["az", "en", "tr"])
        form.addRow("Əsas dil:", self._language_combo)

        self._status_label = QLabel("")
        layout.addLayout(form)
        layout.addWidget(self._status_label)

        save_button = QPushButton("Yadda saxla")
        save_button.clicked.connect(self._save_settings)
        layout.addWidget(save_button)

        clear_memory_button = QPushButton("Yaddaşı təmizlə")
        clear_memory_button.setStyleSheet("color: #dc2626;")
        clear_memory_button.clicked.connect(self._clear_memory)
        layout.addWidget(clear_memory_button)

    def _load_current_settings(self) -> None:
        try:
            resp = httpx.get(f"{API_BASE}/api/settings", timeout=5.0)
            data = resp.json()
            self._provider_combo.setCurrentText(data.get("llm_provider", "local"))
            self._language_combo.setCurrentText(data.get("default_language", "az"))
        except httpx.HTTPError:
            self._status_label.setText("⚠ Serverə qoşula bilmədi")

    def _save_settings(self) -> None:
        try:
            httpx.post(
                f"{API_BASE}/api/settings/provider",
                json={"provider": self._provider_combo.currentText()},
                timeout=5.0,
            )
            self._status_label.setText("✓ Yadda saxlanıldı")
        except httpx.HTTPError as e:
            self._status_label.setText(f"⚠ Xəta: {e}")

    def _clear_memory(self) -> None:
        try:
            httpx.post(f"{API_BASE}/api/settings/memory/clear", timeout=5.0)
            self._status_label.setText("✓ Yaddaş təmizləndi")
        except httpx.HTTPError as e:
            self._status_label.setText(f"⚠ Xəta: {e}")
