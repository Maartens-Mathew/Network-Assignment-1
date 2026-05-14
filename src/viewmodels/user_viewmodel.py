import sys
import asyncio
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.message import ChatMessage
from models.user import User
from repositories.chat_repository import ChatRepository


class UsersViewModel(QObject):
    users_changed = Signal()
    selected_user_changed = Signal()
    messages_changed = Signal()
    loading_changed = Signal(bool)

    def __init__(self, repository: ChatRepository):
        super().__init__()
        self.repository = repository

        self.users: list[User] = []
        self.selected_user: User | None = None
        self.messages: list[ChatMessage] = []

    async def load_users(self):
        self.loading_changed.emit(True)

        try:
            self.users = await self.repository.get_users()
            self.users_changed.emit()
        finally:
            self.loading_changed.emit(False)

    async def select_user(self, user: User):
        self.loading_changed.emit(True)

        try:
            self.selected_user = user
            self.selected_user_changed.emit()

            self.messages = await self.repository.open_dm(user.id)
            self.messages_changed.emit()
        finally:
            self.loading_changed.emit(False)

    async def send_message(self, content: str):
        if self.selected_user is None:
            return

        content = content.strip()
        if not content:
            return

        self.messages = await self.repository.send_dm_message(
            self.selected_user.id,
            content,
        )
        self.messages_changed.emit()