# features/channels/view/channel_screen.py
from __future__ import annotations

from PySide6.QtCore import Qt, QFile, QTextStream
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from features.channels.model.channel import Channel
from features.channels.viewmodel.channel_state import ChannelState
from features.channels.viewmodel.channel_viewmodel import ChannelsViewModel
from features.channels.view.channel_info_dialog import ChannelInfoDialog
from features.channels.view.channel_pages import ChannelPage
import resources_rc
from features.channels.view.items.channel_item import ChannelItemWidget
from features.channels.view.new_channel_dialog import NewChannelDialog
from features.chat.viewmodel.channel_chat_viewmodel import ChannelChatViewModel
from components.chat_panel import ChatPanel


# ─────────────────────────────────────────────────────────────────────────────
# Screen
# ─────────────────────────────────────────────────────────────────────────────

class ChannelScreen(QWidget):
    """
    View layer for channels.

    Responsibilities
    ----------------
    - Build Qt widgets.
    - Forward user intents to ``ChannelsViewModel`` (channel list actions) and
      ``ChannelChatViewModel`` (message display & sending).
    - Render state changes from both view models.
    - Own no business or repository logic.

    The split between the two view models mirrors the split in the UI:
    - Left sidebar  → ``ChannelsViewModel``
    - Right panel   → ``ChannelChatViewModel``
    """

    def __init__(
        self,
        view_model: ChannelsViewModel,
        chat_view_model: ChannelChatViewModel,
    ) -> None:
        super().__init__()

        style_file = QFile(":/auth/styles.qss")

        if style_file.open(QFile.OpenModeFlag.ReadOnly):
            stream = QTextStream(style_file)
            self.setStyleSheet(stream.readAll())
            style_file.close()

        self.view_model = view_model
        self.chat_view_model = chat_view_model
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
        sidebar.setFixedWidth(260)

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
        # Sidebar interactions
        self.channel_list.itemClicked.connect(self._on_channel_item_clicked)
        self.new_channel_button.clicked.connect(self._on_new_channel_clicked)

        # Chat panel
        self.chat_panel.send_clicked.connect(self._on_send_clicked)

        # ChannelsViewModel — drives the left sidebar and navigation
        self.view_model.state_changed.connect(self._on_state_changed)

        # ChannelChatViewModel — drives the right chat panel
        self.chat_view_model.messages_changed.connect(self._render_messages)

    # ── ChannelsViewModel state handler ───────────────────────────────────────

    def _on_state_changed(self, state: ChannelState) -> None:
        match state:
            case ChannelState.LOADING:
                self._show_loading()

            case ChannelState.CHANNELS_LOADED:
                self._render_channels()
                self._show_empty_for_current_channels()

            case ChannelState.CHANNEL_SELECTED:
                # Tell the chat VM which channel we've moved to; it will emit
                # messages_changed and _render_messages will handle the rest.
                channel = self.view_model.selected_channel
                if channel is not None:
                    self.chat_view_model.set_channel(channel)

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
                self.chat_view_model.clear_channel()
                self._show_empty_for_current_channels()

            case ChannelState.CHANNEL_INFO_LOADED:
                self._restore_controls()
                self._show_channel_info_popup()

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
        """
        Called whenever ``ChannelChatViewModel.messages_changed`` fires — both
        on channel switch and on incoming messages.
        """
        messages = self.chat_view_model.get_messages()
        self.chat_panel.set_messages(messages)

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

        await self.chat_view_model.send_message(content)
        self.chat_panel.clear_input()