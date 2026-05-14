import asyncio

from qasync import asyncSlot
from PySide6.QtCore import Qt
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
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.channel import Channel
from state.channel_state import ChannelState
from viewmodels.channel_viewmodel import ChannelsViewModel
from views.reusable.chat_panel import ChatPanel

# ---------------------------------------------------------------------------
# Shared stylesheet
# ---------------------------------------------------------------------------
STYLE = """
    QWidget {
        background-color: #2c3e50;
        color: #ecf0f1;
        font-family: 'Segoe UI', sans-serif;
    }
    QListWidget {
        background-color: #243342;
        border: none;
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        padding: 8px 10px;
        border-radius: 4px;
        color: #bdc3c7;
        font-size: 13px;
    }
    QListWidget::item:hover {
        background-color: #2e4057;
        color: #ecf0f1;
    }
    QListWidget::item:selected {
        background-color: #3498db;
        color: white;
    }
    QPushButton#newChannelBtn {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton#newChannelBtn:hover  { background-color: #2980b9; }
    QPushButton#newChannelBtn:pressed { background-color: #2471a3; }
    QDialog { background-color: #2c3e50; }
    QLabel  { color: #ecf0f1; font-size: 13px; }
    QLineEdit, QTextEdit {
        background-color: #1a252f;
        color: #ecf0f1;
        border: 1px solid #4a6278;
        border-radius: 4px;
        padding: 6px 8px;
        font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #3498db; }
    QPushButton#createBtn {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 7px 18px;
        font-size: 13px;
    }
    QPushButton#createBtn:hover  { background-color: #2980b9; }
    QPushButton#cancelBtn {
        background-color: transparent;
        color: #bdc3c7;
        border: 1px solid #4a6278;
        border-radius: 4px;
        padding: 7px 18px;
        font-size: 13px;
    }
    QPushButton#cancelBtn:hover { background-color: #34495e; }
"""


# ---------------------------------------------------------------------------
# NewChannelDialog
# ---------------------------------------------------------------------------
class NewChannelDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Channel")
        self.setMinimumWidth(380)
        self.setModal(True)
        self.setStyleSheet(STYLE)
        self._build_ui()

    def _build_ui(self):
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

        name_label = QLabel("Channel Name")
        name_label.setStyleSheet("font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. general, announcements")
        self.name_input.setMaxLength(80)
        form.addRow(name_label, self.name_input)

        desc_label = QLabel("Description")
        desc_label.setStyleSheet("font-weight: bold;")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("What is this channel about? (optional)")
        self.desc_input.setFixedHeight(80)
        self.desc_input.setAcceptRichText(False)
        form.addRow(desc_label, self.desc_input)

        layout.addLayout(form)

        # Inline error label — hidden until needed
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Loading label — hidden until needed
        self.loading_label = QLabel("Creating channel…")
        self.loading_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)

        self.create_btn = QPushButton("Create")
        self.create_btn.setObjectName("createBtn")
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._on_create_clicked)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.create_btn)
        layout.addLayout(btn_row)

    def _on_create_clicked(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Channel name cannot be empty.")
            self.name_input.setFocus()
            return
        self.error_label.setVisible(False)
        self.accept()

    # ------------------------------------------------------------------
    # Public helpers called by ChannelScreen based on ViewModel state
    # ------------------------------------------------------------------
    def show_error(self, message: str):
        """Display a server-side or validation error inside the dialog."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.loading_label.setVisible(False)
        self.create_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)

    def set_loading(self, loading: bool):
        """Disable controls and show a status line while the request is in flight."""
        self.loading_label.setVisible(loading)
        self.create_btn.setEnabled(not loading)
        self.cancel_btn.setEnabled(not loading)
        self.name_input.setEnabled(not loading)
        self.desc_input.setEnabled(not loading)

    def get_values(self) -> tuple[str, str]:
        return (
            self.name_input.text().strip(),
            self.desc_input.toPlainText().strip(),
        )


# ---------------------------------------------------------------------------
# ChannelScreen
# ---------------------------------------------------------------------------
class ChannelScreen(QWidget):
    def __init__(self, view_model: ChannelsViewModel):
        super().__init__()
        self.setStyleSheet(STYLE)

        self.view_model = view_model
        self._channel_items: list[Channel] = []
        self._active_dialog: NewChannelDialog | None = None  # kept so states can reach it

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ── Sidebar ────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)

        sidebar_header = QLabel("Channels")
        sidebar_header.setStyleSheet("font-size: 15px; font-weight: bold; padding: 4px 2px;")
        sidebar_layout.addWidget(sidebar_header)

        self.channel_list = QListWidget()
        sidebar_layout.addWidget(self.channel_list)

        self.new_channel_btn = QPushButton("＋  New Channel")
        self.new_channel_btn.setObjectName("newChannelBtn")
        self.new_channel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sidebar_layout.addWidget(self.new_channel_btn)

        # ── Main area: stacked between loading overlay and chat panel ──
        self.stack = QStackedWidget()

        # Page 0 — loading
        loading_page = QWidget()
        loading_layout = QVBoxLayout(loading_page)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label = QLabel("Loading…")
        self.loading_label.setStyleSheet("color: #95a5a6; font-size: 15px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        self.stack.addWidget(loading_page)   # index 0

        # Page 1 — empty / placeholder
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Select a channel to start chatting")
        hint.setStyleSheet("color: #4a6278; font-size: 14px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint)
        self.stack.addWidget(empty_page)     # index 1

        # Page 2 — chat panel
        self.chat_panel = ChatPanel()
        self.stack.addWidget(self.chat_panel)  # index 2

        self.stack.setCurrentIndex(1)  # default: empty

        # ── Root layout ────────────────────────────────────────────────
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(sidebar)
        root.addWidget(self.stack, 1)

    def _connect_signals(self):
        self.channel_list.itemClicked.connect(self.on_channel_clicked)
        self.chat_panel.send_clicked.connect(self.on_send_clicked)
        self.new_channel_btn.clicked.connect(self.on_new_channel_clicked)
        self.view_model.state_changed.connect(self.on_state_changed)

    # ------------------------------------------------------------------
    # State handler
    # ------------------------------------------------------------------
    def on_state_changed(self, state: ChannelState):
        match state:
            case ChannelState.LOADING:
                self._show_loading()

            case ChannelState.CHANNELS_LOADED:
                self._render_channel_list()
                self.stack.setCurrentIndex(1)   # show empty/hint until a channel is picked

            case ChannelState.CHANNEL_SELECTED:
                self._render_selected_channel()
                self._render_messages()
                self.stack.setCurrentIndex(2)   # show chat panel

            case ChannelState.CHANNEL_CREATED:
                self._close_dialog()
                self._render_channel_list()

            case ChannelState.ERROR:
                self.stack.setCurrentIndex(1)   # stop showing spinner
                if self._active_dialog is not None:
                    # Error belongs to the dialog flow — show it inline
                    self._active_dialog.show_error(self.view_model.error or "Unknown error")
                else:
                    QMessageBox.critical(self, "Error", self.view_model.error or "Unknown error")

    # ------------------------------------------------------------------
    # Render helpers
    # ------------------------------------------------------------------
    def _show_loading(self):
        if self._active_dialog is not None:
            self._active_dialog.set_loading(True)
        else:
            self.stack.setCurrentIndex(0)

    def _render_channel_list(self):
        self.channel_list.clear()
        self._channel_items.clear()

        for channel in self.view_model.channels:
            item = QListWidgetItem(f"# {channel.name}")
            item.setData(Qt.ItemDataRole.UserRole, channel.name)  # name as key
            self.channel_list.addItem(item)
            self._channel_items.append(channel)  # dict keyed by name

    def _render_selected_channel(self):
        channel = self.view_model.selected_channel
        if channel:
            self.chat_panel.set_title(f"# {channel.name}")

    def _render_messages(self):
        print("render messages")
        # self.chat_panel.set_messages(self.view_model.)

    def _close_dialog(self):
        if self._active_dialog is not None:
            self._active_dialog.accept()
            self._active_dialog = None

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    @asyncSlot()
    async def load(self):
        await self.view_model.load_channels()

    def on_new_channel_clicked(self):
        dialog = NewChannelDialog(parent=self)
        self._active_dialog = dialog

        result = dialog.exec()

        # User cancelled before the request completed — clear the reference
        if result != QDialog.DialogCode.Accepted:
            self._active_dialog = None
            return

        name, description = dialog.get_values()
        asyncio.ensure_future(self.view_model.create_channel(name, description))

    @asyncSlot(QListWidgetItem)
    async def on_channel_clicked(self, item: QListWidgetItem):
        channel_name = item.data(Qt.ItemDataRole.UserRole)
        if channel_name:
            await self.view_model.select_channel(channel_name)

    @asyncSlot(str)
    async def on_send_clicked(self, content: str):
        # await self.view_model.send_message(content)
        self.chat_panel.clear_input()