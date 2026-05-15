from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from models.channel import Channel
from state.channel_state import ChannelState
from viewmodels.channel_viewmodel import ChannelsViewModel
from views.channel_screen.channel_info_dialog import ChannelInfoDialog
from views.channel_screen.channel_pages import ChannelPage
from views.channel_screen.channel_styles import STYLE
from views.channel_screen.new_channel_dialog import NewChannelDialog
from views.reusable.chat_panel import ChatPanel


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


# ─────────────────────────────────────────────────────────────────────────────
# Screen
# ─────────────────────────────────────────────────────────────────────────────

class ChannelScreen(QWidget):
    """
    View layer for channels.

    Responsibilities:
    - Build Qt widgets.
    - Forward user intents to ChannelsViewModel.
    - Render ViewModel state.
    - Avoid owning business logic or repository logic.
    """

    def __init__(self, view_model: ChannelsViewModel):
        super().__init__()
        self.setStyleSheet(STYLE)

        self.view_model = view_model
        self._active_dialog: NewChannelDialog | None = None

        self._build_ui()
        self._connect_signals()
        self._show_empty("Select a channel to start chatting")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content_stack(), 1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(260)          # slightly wider to fit the three buttons

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QLabel("Channels")
        header.setStyleSheet("font-size: 15px; font-weight: bold; padding: 4px 2px;")
        layout.addWidget(header)

        self.channel_list = QListWidget()
        self.channel_list.setSpacing(2)
        layout.addWidget(self.channel_list, 1)

        self.new_channel_button = QPushButton("＋  New Channel")
        self.new_channel_button.setObjectName("newChannelBtn")
        self.new_channel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.new_channel_button)

        return sidebar

    def _build_content_stack(self) -> QStackedWidget:
        self.stack = QStackedWidget()

        self.loading_label = QLabel("Loading…")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #95a5a6; font-size: 15px;")
        self.stack.addWidget(self._centered_page(self.loading_label))

        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #4a6278; font-size: 14px;")
        self.empty_label.setWordWrap(True)
        self.stack.addWidget(self._centered_page(self.empty_label))

        self.chat_panel = ChatPanel()
        self.stack.addWidget(self.chat_panel)

        return self.stack

    def _centered_page(self, widget: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)
        return page

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self.channel_list.itemClicked.connect(self._on_channel_item_clicked)
        self.new_channel_button.clicked.connect(self._on_new_channel_clicked)
        self.chat_panel.send_clicked.connect(self._on_send_clicked)
        self.view_model.state_changed.connect(self._on_state_changed)

    # ── State handler ─────────────────────────────────────────────────────────

    def _on_state_changed(self, state: ChannelState) -> None:
        match state:
            case ChannelState.LOADING:
                self._show_loading()

            case ChannelState.CHANNELS_LOADED:
                self._render_channels()
                self._show_empty_for_current_channels()

            case ChannelState.CHANNEL_SELECTED:
                self._render_selected_channel()
                self._show_chat()

            case ChannelState.CHANNEL_JOINED:
                self._render_channels()
                self._show_empty_for_current_channels()

            case ChannelState.CHANNEL_CREATED:
                self._render_channels()
                self._close_create_dialog()
                self._show_empty_for_current_channels()

            case ChannelState.CHANNEL_LEFT:
                self._render_channels()
                self._show_empty_for_current_channels()

            case ChannelState.CHANNEL_INFO_LOADED:
                self._restore_controls()
                self._show_channel_info_popup()

            case ChannelState.MESSAGES_LOADED:
                self._render_messages()
                self._show_chat()

            case ChannelState.ERROR:
                self._show_error(self.view_model.error or "Unknown error")

    # ── Visibility helpers ────────────────────────────────────────────────────

    def _show_loading(self) -> None:
        if self._active_dialog is not None and self._active_dialog.isVisible():
            self._active_dialog.set_loading(True)
            return

        self.channel_list.setEnabled(False)
        self.new_channel_button.setEnabled(False)
        self.stack.setCurrentIndex(ChannelPage.LOADING)

    def _restore_controls(self) -> None:
        self.channel_list.setEnabled(True)
        self.new_channel_button.setEnabled(True)

    def _show_empty_for_current_channels(self) -> None:
        self._restore_controls()

        if not self.view_model.channels:
            self._show_empty("No channels yet. Create one to get started.")
        elif self.view_model.selected_channel is None:
            self._show_empty("Select a channel to start chatting")
        else:
            self._show_chat()

    def _show_empty(self, message: str) -> None:
        self.empty_label.setText(message)
        self.stack.setCurrentIndex(ChannelPage.EMPTY)

    def _show_chat(self) -> None:
        self._restore_controls()
        self.stack.setCurrentIndex(ChannelPage.CHAT)

    def _show_error(self, message: str) -> None:
        self._restore_controls()

        if self._active_dialog is not None and self._active_dialog.isVisible():
            self._active_dialog.show_error(message)
            return

        self._show_empty_for_current_channels()
        QMessageBox.critical(self, "Channel error", message)

    def _show_channel_info_popup(self) -> None:
        info = self.view_model.channel_info
        if info is None:
            return

        dialog = ChannelInfoDialog(info, parent=self)
        dialog.exec()

    # ── Render helpers ────────────────────────────────────────────────────────

    def _render_channels(self) -> None:
        selected_name = (
            self.view_model.selected_channel.name
            if self.view_model.selected_channel
            else None
        )

        self.channel_list.blockSignals(True)
        self.channel_list.clear()

        for channel in self.view_model.channels:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, channel)

            item_widget = ChannelItemWidget(channel)
            item_widget.join_clicked.connect(self._on_join_clicked)
            item_widget.leave_clicked.connect(self._on_leave_clicked)
            item_widget.info_clicked.connect(self._on_info_clicked)

            item.setSizeHint(item_widget.sizeHint())
            self.channel_list.addItem(item)
            self.channel_list.setItemWidget(item, item_widget)

            if channel.name == selected_name:
                self.channel_list.setCurrentItem(item)

        self.channel_list.blockSignals(False)

    def _render_selected_channel(self) -> None:
        channel = self.view_model.selected_channel
        if channel is None:
            self._show_empty_for_current_channels()
            return

        self.chat_panel.set_title(f"# {channel.name}")
        self._select_channel_in_list(channel)

    def _select_channel_in_list(self, selected: Channel) -> None:
        for index in range(self.channel_list.count()):
            item = self.channel_list.item(index)
            channel = item.data(Qt.ItemDataRole.UserRole)

            if isinstance(channel, Channel) and channel.name == selected.name:
                self.channel_list.setCurrentItem(item)
                return

    def _render_messages(self) -> None:
        # Intentionally empty until ChannelsViewModel exposes messages.
        # Once available:
        #     self.chat_panel.set_messages(self.view_model.messages)
        pass

    def _close_create_dialog(self) -> None:
        if self._active_dialog is None:
            return

        dialog = self._active_dialog
        self._active_dialog = None

        dialog.set_loading(False)
        dialog.accept()

    # ── Slots ─────────────────────────────────────────────────────────────────

    @asyncSlot()
    async def load(self) -> None:
        await self.view_model.load_channels()

    def _on_new_channel_clicked(self) -> None:
        if self._active_dialog is not None and self._active_dialog.isVisible():
            self._active_dialog.raise_()
            self._active_dialog.activateWindow()
            return

        dialog = NewChannelDialog(parent=self)
        dialog.create_requested.connect(self._on_create_channel_requested)
        dialog.finished.connect(self._on_create_dialog_finished)

        self._active_dialog = dialog
        dialog.open()

    def _on_create_dialog_finished(self) -> None:
        self._active_dialog = None

    @asyncSlot(str, str)
    async def _on_create_channel_requested(self, name: str, description: str) -> None:
        await self.view_model.create_channel(name, description)

    @asyncSlot(QListWidgetItem)
    async def _on_channel_item_clicked(self, item: QListWidgetItem) -> None:
        """
        Clicking the row itself (outside the buttons) selects the channel.
        Button clicks are handled by the item widget's own signals.
        """
        channel = item.data(Qt.ItemDataRole.UserRole)

        if not isinstance(channel, Channel):
            return

        if self.view_model.selected_channel == channel:
            return

        await self.view_model.select_channel(channel)

    @asyncSlot(Channel)
    async def _on_join_clicked(self, channel: Channel) -> None:
        await self.view_model.join_channel(channel)

    @asyncSlot(Channel)
    async def _on_leave_clicked(self, channel: Channel) -> None:
        await self.view_model.leave_channel(channel)

    @asyncSlot(Channel)
    async def _on_info_clicked(self, channel: Channel) -> None:
        await self.view_model.get_channel_info(channel)

    @asyncSlot(str)
    async def _on_send_clicked(self, content: str) -> None:
        content = content.strip()

        if not content:
            return

        # Uncomment once ChannelsViewModel exposes send_message(content).
        # await self.view_model.send_message(content)

        self.chat_panel.clear_input()