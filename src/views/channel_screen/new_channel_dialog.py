from __future__ import annotations

from enum import IntEnum

from qasync import asyncSlot
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from views.channel_screen.channel_styles import STYLE


class NewChannelDialog(QDialog):
    """
    Small view-only dialog.

    It validates local input and emits create_requested. It does not call the
    ViewModel directly, which keeps the dialog reusable and easy to test.
    """

    create_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Channel")
        self.setMinimumWidth(380)
        self.setModal(True)
        self.setStyleSheet(STYLE)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        header = QLabel("Create a channel")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        subtitle = QLabel("Channels are where conversations happen around a topic.")
        subtitle.setStyleSheet("color: #95a5a6; font-size: 12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. general, announcements")
        self.name_input.setMaxLength(80)
        form.addRow(self._form_label("Channel Name"), self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("What is this channel about? (optional)")
        self.description_input.setFixedHeight(80)
        self.description_input.setAcceptRichText(False)
        form.addRow(self._form_label("Description"), self.description_input)

        layout.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelBtn")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)

        self.create_button = QPushButton("Create")
        self.create_button.setObjectName("createBtn")
        self.create_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_button.setDefault(True)
        self.create_button.clicked.connect(self._on_create_clicked)

        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.create_button)
        layout.addLayout(button_row)

    def _form_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")
        return label

    def _on_create_clicked(self) -> None:
        name, description = self.values()

        if not name:
            self.show_error("Channel name cannot be empty.")
            self.name_input.setFocus()
            return

        self.clear_status()
        self.create_requested.emit(name, description)

    def values(self) -> tuple[str, str]:
        return (
            self.name_input.text().strip(),
            self.description_input.toPlainText().strip(),
        )

    def set_loading(self, loading: bool) -> None:
        self.status_label.setText("Creating channel…")
        self.status_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        self.status_label.setVisible(loading)

        self.name_input.setEnabled(not loading)
        self.description_input.setEnabled(not loading)
        self.create_button.setEnabled(not loading)
        self.cancel_button.setEnabled(not loading)

    def show_error(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        self.status_label.setVisible(True)

        self.name_input.setEnabled(True)
        self.description_input.setEnabled(True)
        self.create_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def clear_status(self) -> None:
        self.status_label.clear()
        self.status_label.setVisible(False)