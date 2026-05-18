from PySide6.QtCore import QObject, Signal

from features.channels.model.channel import Channel
from features.chat.model.message import ChatMessage, UserMessage
from features.chat.repository.chat_repository import ChatRepository
from features.users.model.user import User


class UserChatViewModel(QObject):
    chat_repository : ChatRepository
    on_user_updated = Signal()
    current_user : User


    def __init__(self, chat_repository : ChatRepository):
        super().__init__()
        self.chat_repository = chat_repository

        chat_repository.on_new_user_message.connect(
            self._on_user_message_received
        )

    def _on_user_message_received(self, message : UserMessage):
        self.on_user_updated.emit()


    def get_messages(self, user : User):
        return self.chat_repository.get_user_messages(user)




