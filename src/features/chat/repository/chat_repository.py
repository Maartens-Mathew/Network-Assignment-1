# features/chat/repository/chat_repository.py
from PySide6.QtCore import QObject, Signal

from features.channels.model.channel import Channel
from features.chat.model.message import ChatMessage, UserMessage
from features.users.model.user import User
from network_client.chat_protocol import ChatProtocol


class ChatRepository(QObject):
    """
    Thin cache layer between the network protocol and the rest of the app.

    Signals
    -------
    on_new_channel_message  Emitted whenever a channel message arrives from the
                            protocol.  Listeners receive the full ChatMessage.
    on_new_user_message     Emitted whenever a direct/user message arrives.
    """

    on_new_channel_message = Signal(ChatMessage)
    on_new_user_message = Signal(UserMessage)

    def __init__(self, client: ChatProtocol):
        super().__init__()                          # Required: QObject init
        self._channel_messages: dict[Channel, list[ChatMessage]] = {}
        self._user_conversations: dict[User, list[UserMessage]] = {}

        self._chat_protocol = client
        self._chat_protocol.channel_message_received.connect(self._on_channel_message_received)
        self._chat_protocol.user_message_received.connect(self._on_user_message_received)

    # ── Protocol callbacks ────────────────────────────────────────────────────

    def _on_channel_message_received(self, message: ChatMessage) -> None:
        bucket = self._channel_messages.setdefault(message.channel, [])
        bucket.append(message)
        self.on_new_channel_message.emit(message)   # Forward to subscribers

    def _on_user_message_received(self, message: UserMessage) -> None:
        bucket = self._user_conversations.setdefault(message.sender, [])
        bucket.append(message)
        self.on_new_user_message.emit(message)

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_channel_messages(self, channel: Channel) -> list[ChatMessage]:
        return self._channel_messages.get(channel, [])

    def get_user_messages(self, user: User) -> list[UserMessage]:
        return self._user_conversations.get(user, [])

    # ── Commands ──────────────────────────────────────────────────────────────

    async def send_channel_message(self, channel: Channel, content: str) -> None:
        """Send a message to *channel* via the underlying protocol."""
        await self._chat_protocol.send_channel_message(channel, content)

    async def send_user_message(self, recipient: User, content: str) -> None:
        """Send a direct message to *recipient* via the underlying protocol."""
        await self._chat_protocol.send_user_message(recipient, content)