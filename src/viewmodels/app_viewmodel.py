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

from core.keystore.key_store import KeyStore
from models.app_section import AppSection
from models.user import User
from repositories.chat_repository import ChatRepository


class AppViewModel(QObject):
    current_section_changed = Signal()
    current_user_changed = Signal()
    key_values_show = Signal(dict)

    def __init__(self, repository: ChatRepository):
        super().__init__()
        self.repository = repository

        self.current_section = AppSection.CHANNELS
        self.current_user: User | None = None

    async def load_current_user(self):
        self.current_user = await self.repository.get_current_user()
        self.current_user_changed.emit()

    def go_to_channels(self):
        self.current_section = AppSection.CHANNELS
        self.current_section_changed.emit()

    def go_to_users(self):
        self.current_section = AppSection.USERS
        self.current_section_changed.emit()

    def get_entries(self):
        keystore = KeyStore(app_name="chat_client", password=b"csc4026")
        entries = keystore.load()
        self.key_values_show.emit(entries)