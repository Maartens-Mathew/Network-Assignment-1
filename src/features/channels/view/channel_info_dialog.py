# views/channel_screen/channel_info_dialog.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from features.channels.model.channel import ChannelDetailed


class ChannelInfoDialog(QDialog):
    """
    Read-only popup showing the name and description of a channel.

    Usage:
        dialog = ChannelInfoDialog(channel_info, parent=self)
        dialog.exec()
    """

    def __init__(self, channel_info: ChannelDetailed, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Channel Info")
        self.setMinimumWidth(340)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Channel name ──────────────────────────────────────────────
        name_label = QLabel(f"# {channel_info.name}")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name_label.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #ecf0f1;"
        )
        layout.addWidget(name_label)

        # ── Divider ───────────────────────────────────────────────────
        divider = QLabel()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #4a6278;")
        layout.addWidget(divider)

        # ── Description ───────────────────────────────────────────────
        description_text = channel_info.description or "No description provided."
        desc_label = QLabel(description_text)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        desc_label.setStyleSheet("color: #bdc3c7; font-size: 13px; line-height: 1.5;")
        desc_label.setMinimumHeight(60)
        layout.addWidget(desc_label)

        layout.addStretch()

        # ── Close button ──────────────────────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.setObjectName("cancelBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)