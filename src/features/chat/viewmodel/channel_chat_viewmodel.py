# features/chat/viewmodel/channel_chat_viewmodel.py
from PySide6.QtCore import QObject, Signal

from features.channels.model.channel import Channel
from features.chat.model.message import ChatMessage
from features.chat.repository.chat_repository import ChatRepository


class ChannelChatViewModel(QObject):
    """
    View model for the chat panel on the right side of ChannelScreen.

    Responsibilities
    ----------------
    - Track which channel is currently open.
    - Maintain (via the repository) the ordered list of messages for that channel.
    - Emit ``messages_changed`` whenever the view should re-render the message list,
      whether because the user switched channels or a new message arrived.

    The view never reads the repository directly; it always asks this VM for
    the current message list via ``get_messages()``.
    """

    messages_changed = Signal()

    def __init__(self, chat_repository: ChatRepository) -> None:
        super().__init__()
        self._chat_repository = chat_repository
        self.current_channel: Channel | None = None

        self._chat_repository.on_new_channel_message.connect(
            self._on_channel_message_received
        )

    # ── Channel lifecycle ─────────────────────────────────────────────────────

    def set_channel(self, channel: Channel) -> None:
        """Switch the active channel and immediately refresh the message list."""
        self.current_channel = channel
        self.messages_changed.emit()

    def clear_channel(self) -> None:
        """Called when no channel is selected (e.g. after leaving one)."""
        self.current_channel = None

    # ── Repository callback ───────────────────────────────────────────────────

    def _on_channel_message_received(self, message: ChatMessage) -> None:
        """
        Only propagate the signal if the message belongs to the channel the
        user is currently looking at.  Messages for other channels are still
        persisted by the repository; we just don't disturb the UI.
        """
        if self.current_channel is None:
            return

        if message.channel.name == self.current_channel.name:
            self.messages_changed.emit()

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_messages(self) -> list[ChatMessage]:
        """Return the message list for the active channel, or [] if none."""
        if self.current_channel is None:
            return []
        return self._chat_repository.get_channel_messages(self.current_channel)

    # ── Commands ──────────────────────────────────────────────────────────────

    async def send_message(self, content: str) -> None:
        """
        Send *content* to the current channel.
        No-ops silently if no channel is active (the view should guard this
        with a disabled send button, but defence-in-depth doesn't hurt).
        """
        if self.current_channel is None:
            return
        await self._chat_repository.send_channel_message(self.current_channel, content)