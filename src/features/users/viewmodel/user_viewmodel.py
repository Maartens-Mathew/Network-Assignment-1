from PySide6.QtCore import QObject, Signal, Property
from qasync import asyncSlot

from features.chat.model.message import ChatMessage
from features.users.model.user import User
from features.chat.repository.chat_repository import ChatRepository
from features.users.repository.user_repository import UserRepository


class UsersViewModel(QObject):
    users_changed = Signal()
    selected_user_changed = Signal()
    messages_changed = Signal()
    loading_changed = Signal(bool)

    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self.user_repository = user_repository

        self._users: list[User] = []
        self._selected_user: User | None = None
        self._messages: list[ChatMessage] = []

    @Property("QVariant", notify=users_changed)
    def users(self):
        return self._users

    @Property("QVariant", notify=selected_user_changed)
    def selected_user(self):
        return self._selected_user

    @Property("QVariant", notify=messages_changed)
    def messages(self):
        return self._messages

    @asyncSlot()
    async def load_users(self):
        self.loading_changed.emit(True)

        try:
            self._users = await self.user_repository.get_users()
            self.users_changed.emit()
        finally:
            self.loading_changed.emit(False)

    @asyncSlot(QObject)
    async def select_user(self, user: User):
        self.loading_changed.emit(True)

        try:
            self._selected_user = user
            self.selected_user_changed.emit()

            # self._messages = await self.repository.open_dm(user.id)
            self.messages_changed.emit()
        finally:
            self.loading_changed.emit(False)

    @asyncSlot(str)
    async def send_message(self, content: str):
        if self._selected_user is None:
            return

        content = content.strip()
        if not content:
            return

        # self._messages = await self.repository.send_dm_message(
        #     self._selected_user.id,
        #     content,
        # )
        self.messages_changed.emit()