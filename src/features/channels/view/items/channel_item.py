from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from features.channels.model.channel import Channel


# ─────────────────────────────────────────────────────────────────────────────
# Per-item widget
# ─────────────────────────────────────────────────────────────────────────────

class ChannelItemWidget(QWidget):
    """
    A single row in the channel sidebar.

    Layout:  [# name ──────────────]  [ⓘ]  [Join]  [Leave]

    Signals are emitted with the Channel the row represents, so the
    screen can forward them directly to the ViewModel without needing
    to know which row was clicked.
    """

    join_clicked  = Signal(Channel)
    leave_clicked = Signal(Channel)
    info_clicked  = Signal(Channel)

    def __init__(self, channel: Channel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.channel = channel

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(5)

        # Channel name label
        name = QLabel(f"# {channel.name}")
        name.setStyleSheet("font-size: 13px; color: #bdc3c7;")
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(name)

        # ⓘ info button
        info_btn = QPushButton("ⓘ")
        info_btn.setObjectName("infoBtn")
        info_btn.setFixedSize(26, 26)
        info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        info_btn.setToolTip("Channel info")
        info_btn.clicked.connect(lambda: self.info_clicked.emit(self.channel))
        layout.addWidget(info_btn)

        # Join button
        join_btn = QPushButton("Join")
        join_btn.setObjectName("joinBtn")
        join_btn.setFixedSize(48, 26)
        join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        join_btn.setToolTip("Join this channel")
        join_btn.clicked.connect(lambda: self.join_clicked.emit(self.channel))
        layout.addWidget(join_btn)

        # Leave button
        leave_btn = QPushButton("Leave")
        leave_btn.setObjectName("leaveBtn")
        leave_btn.setFixedSize(52, 26)
        leave_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        leave_btn.setToolTip("Leave this channel")
        leave_btn.clicked.connect(lambda: self.leave_clicked.emit(self.channel))
        layout.addWidget(leave_btn)