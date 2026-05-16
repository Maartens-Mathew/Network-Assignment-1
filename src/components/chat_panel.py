from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from features.chat.model.message import ChatMessage


class ChatPanel(QWidget):
    """
    Reusable right-side chat panel.

    Used by both:
    - ChannelScreen
    - UserScreen
    """

    send_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        self.title_label = QLabel("Select something to begin")
        self.title_label.setObjectName("ChatTitle")

        self.messages_view = QTextEdit()
        self.messages_view.setReadOnly(True)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")

        self.send_button = QPushButton("Send")

        input_row = QHBoxLayout()
        input_row.addWidget(self.message_input)
        input_row.addWidget(self.send_button)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.messages_view)
        layout.addLayout(input_row)

        self.setLayout(layout)

        self.send_button.clicked.connect(self._on_send_clicked)
        self.message_input.returnPressed.connect(self._on_send_clicked)

    def set_title(self, title: str):
        self.title_label.setText(title)

    def set_messages(self, messages: list[ChatMessage]):
        lines = []

        for message in messages:
            lines.append(f"<b>{message.sender_name}:</b> {message.content}")

        self.messages_view.setHtml("<br><br>".join(lines))

    def clear_input(self):
        self.message_input.clear()

    def _on_send_clicked(self):
        self.send_clicked.emit(self.message_input.text())