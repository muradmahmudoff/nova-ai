"""
Nova AI - Əsas Pəncərə
==========================
Desktop tətbiqinin giriş nöqtəsi. Chat widget, mikrofon düyməsi və
parametrlər menyusunu birləşdirir. Backend (FastAPI) ilə HTTP üzərindən
əlaqə saxlayır - GUI və server ayrı proseslər kimi işləyir ki, backend-i
CLI/başqa müştərilərdən də istifadə etmək mümkün olsun.

İşə salmaq: python scripts/run_gui.py
"""
from __future__ import annotations

import sys

import httpx
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMessageBox

from app.gui.chat_widget import ChatWidget
from app.gui.settings_dialog import SettingsDialog

API_BASE = "http://127.0.0.1:8000"


class ChatWorker(QThread):
    """Backend-ə HTTP sorğusunu ayrı thread-də edir ki, GUI donmasın (bloklanmasın)."""

    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, conversation_id: str | None, message: str):
        super().__init__()
        self._conversation_id = conversation_id
        self._message = message

    def run(self) -> None:
        try:
            resp = httpx.post(
                f"{API_BASE}/api/chat",
                json={"conversation_id": self._conversation_id, "message": self._message},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            self.response_ready.emit(data["response"])
            self._new_conversation_id = data["conversation_id"]
        except httpx.HTTPError as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova - Şəxsi AI Köməkçim")
        self.resize(720, 800)
        self.setStyleSheet("background-color: #18181b;")

        self._conversation_id: str | None = None
        self._worker: ChatWorker | None = None

        self._chat_widget = ChatWidget(on_send_message=self._handle_send_message)
        self.setCentralWidget(self._chat_widget)

        self._build_menu()
        self._chat_widget.add_message(
            "Salam! Mən Nova, sənin şəxsi AI köməkçinəm. Necə kömək edə bilərəm?",
            is_user=False,
        )

    def _build_menu(self) -> None:
        menu_bar: QMenuBar = self.menuBar()
        settings_menu = menu_bar.addMenu("Parametrlər")
        open_settings_action = settings_menu.addAction("Aç...")
        open_settings_action.triggered.connect(self._open_settings)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def _handle_send_message(self, text: str) -> None:
        self._worker = ChatWorker(self._conversation_id, text)
        self._worker.response_ready.connect(self._handle_response)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.start()

    def _handle_response(self, response_text: str) -> None:
        if self._worker is not None:
            self._conversation_id = getattr(self._worker, "_new_conversation_id", self._conversation_id)
        self._chat_widget.add_message(response_text, is_user=False)

    def _handle_error(self, error_message: str) -> None:
        QMessageBox.warning(
            self,
            "Bağlantı xətası",
            f"Backend-ə qoşula bilmədi. Server işə salınıb?\n\nXəta: {error_message}",
        )


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
