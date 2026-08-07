"""
Nova AI - Mikrofon Düyməsi
==============================
Basılı saxlanılanda (yaxud toggle) mikrofon axınını başladan/dayandıran düymə.
Vizual olaraq dinləmə vəziyyətini (idle/listening/processing) göstərir.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton


class MicButton(QPushButton):
    """Üç vəziyyəti olan mikrofon düyməsi: idle, listening, processing."""

    listening_started = Signal()
    listening_stopped = Signal()

    _STYLES = {
        "idle": "background-color: #3f3f46; color: white; border-radius: 24px; font-size: 18px;",
        "listening": "background-color: #dc2626; color: white; border-radius: 24px; font-size: 18px;",
        "processing": "background-color: #ca8a04; color: white; border-radius: 24px; font-size: 18px;",
    }

    def __init__(self):
        super().__init__("🎙")
        self.setFixedSize(48, 48)
        self._state = "idle"
        self._apply_style()
        self.clicked.connect(self._toggle)

    def _toggle(self) -> None:
        if self._state == "idle":
            self.set_state("listening")
            self.listening_started.emit()
        elif self._state == "listening":
            self.set_state("processing")
            self.listening_stopped.emit()

    def set_state(self, state: str) -> None:
        """Xarici kod (audio pipeline callback-i) bu funksiyanı çağırıb vəziyyəti yeniləyir."""
        if state not in self._STYLES:
            return
        self._state = state
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(self._STYLES[self._state])
