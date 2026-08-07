"""
Nova AI - Chat Widget
=========================
Söhbət mesajlarının göstərildiyi əsas pəncərə hissəsi.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QFrame,
)


class MessageBubble(QFrame):
    """Tək bir mesaj "bulionu" - istifadəçi (sağda) və ya Nova (solda)."""

    def __init__(self, text: str, is_user: bool):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet(
            f"""
            background-color: {'#2563eb' if is_user else '#27272a'};
            color: white;
            padding: 10px 14px;
            border-radius: 14px;
            font-size: 14px;
            """
        )
        label.setMaximumWidth(480)

        if is_user:
            layout.addStretch()
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch()


class ChatWidget(QWidget):
    """Mesajları göstərən scroll-lanan sahə + input xətti."""

    def __init__(self, on_send_message):
        """
        Args:
            on_send_message: callback(text: str) -> None, istifadəçi mesaj göndərdikdə çağırılır
        """
        super().__init__()
        self._on_send_message = on_send_message
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---- Mesaj siyahısı (scroll edilə bilən) ----
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet("background-color: #18181b; border: none;")

        self._messages_container = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.addStretch()
        self._scroll_area.setWidget(self._messages_container)

        main_layout.addWidget(self._scroll_area)

        # ---- Aşağı panel: input + göndər + mikrofon ----
        input_bar = QHBoxLayout()
        input_bar.setContentsMargins(10, 10, 10, 10)

        self._input_line = QLineEdit()
        self._input_line.setPlaceholderText("Nova-ya mesaj yaz...")
        self._input_line.setStyleSheet(
            "padding: 10px; border-radius: 10px; background-color: #27272a; color: white; font-size: 14px;"
        )
        self._input_line.returnPressed.connect(self._handle_send)

        send_button = QPushButton("Göndər")
        send_button.setStyleSheet(
            "background-color: #2563eb; color: white; padding: 10px 18px; border-radius: 10px;"
        )
        send_button.clicked.connect(self._handle_send)

        input_bar.addWidget(self._input_line)
        input_bar.addWidget(send_button)

        main_layout.addLayout(input_bar)

    def _handle_send(self) -> None:
        text = self._input_line.text().strip()
        if not text:
            return
        self.add_message(text, is_user=True)
        self._input_line.clear()
        self._on_send_message(text)

    def add_message(self, text: str, is_user: bool) -> None:
        """Yeni mesaj bulionu əlavə edir və aşağı scroll edir."""
        bubble = MessageBubble(text, is_user)
        # addStretch elementindən əvvəl əlavə et ki, mesajlar yuxarıdan aşağı düzülsün
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, bubble)

        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
