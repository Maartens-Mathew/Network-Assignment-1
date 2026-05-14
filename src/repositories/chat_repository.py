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

from models.channel import Channel
from models.message import ChatMessage
from models.user import User


class ChatRepository:
    """
    Dummy repository.

    In a real app, this would call your server over TCP/WebSocket/HTTP.
    For now, we use asyncio.sleep(...) to simulate request-response latency.
    """

    def __init__(self):
        self._current_user = User(
            username="mathew"
        )

        self._channels = [
            Channel("general"),
            Channel("python"),
            Channel("qt-pyside"),
            Channel("random"),
        ]

        self._users = [
            User("alice"),
            User("bob"),
            User("carla"),
            User("david"),
        ]

        self._channel_messages = {
            1: [
                ChatMessage("Alice", "Welcome to general."),
                ChatMessage("Bob", "Hey everyone."),
            ],
            2: [
                ChatMessage("Carla", "Has anyone tried asyncio with PySide6?"),
                ChatMessage("Mathew", "Yes, qasync works nicely for that."),
            ],
            3: [
                ChatMessage("David", "QStackedWidget is useful for navigation."),
            ],
            4: [
                ChatMessage("Alice", "Anyone playing anything interesting?"),
            ],
        }

        self._dm_messages = {
            2: [
                ChatMessage("Alice", "Hey Mathew."),
                ChatMessage("Mathew", "Hey Alice."),
            ],
            3: [
                ChatMessage("Bob", "Can you review my Python code later?"),
            ],
            4: [
                ChatMessage("Carla", "The UI mockup looks good."),
            ],
            5: [],
        }

    async def login(self, username: str, password: str) -> User:
        await asyncio.sleep(0.5)

        # Dummy login rule.
        # Any non-empty username/password is accepted.
        if not username.strip() or not password.strip():
            raise ValueError("Username and password are required.")

        return self._current_user

    async def get_current_user(self) -> User:
        await asyncio.sleep(0.2)
        return self._current_user

    async def get_channels(self) -> list[Channel]:
        await asyncio.sleep(0.4)
        return self._channels

    async def get_users(self) -> list[User]:
        await asyncio.sleep(0.4)
        return self._users

    async def join_channel(self, channel_id: int) -> list[ChatMessage]:
        await asyncio.sleep(0.4)
        return self._channel_messages.get(channel_id, [])

    async def open_dm(self, user_id: int) -> list[ChatMessage]:
        await asyncio.sleep(0.4)
        return self._dm_messages.get(user_id, [])

    async def send_channel_message(self, channel_id: int, content: str) -> list[ChatMessage]:
        await asyncio.sleep(0.25)

        message = ChatMessage("Mathew", content)
        self._channel_messages.setdefault(channel_id, []).append(message)

        return self._channel_messages[channel_id]

    async def send_dm_message(self, user_id: int, content: str) -> list[ChatMessage]:
        await asyncio.sleep(0.25)

        message = ChatMessage("Mathew", content)
        self._dm_messages.setdefault(user_id, []).append(message)

        return self._dm_messages[user_id]