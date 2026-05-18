from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QWidget,
)
from qasync import asyncSlot

from features.users.model.user import User
from features.users.viewmodel.user_viewmodel import UsersViewModel
from components.chat_panel import ChatPanel


class UserScreen(QWidget):
    def __init__(self, view_model: UsersViewModel):
        super().__init__()

        self.view_model = view_model
        self._user_items: dict[int, User] = {}

        self.user_list = QListWidget()
        self.user_list.setObjectName("SideList")

        self.chat_panel = ChatPanel()

        layout = QHBoxLayout()
        layout.addWidget(self.user_list, 1)
        layout.addWidget(self.chat_panel, 3)

        self.setLayout(layout)

        self.user_list.itemClicked.connect(self.on_user_clicked)
        self.chat_panel.send_clicked.connect(self.on_send_clicked)

        self.view_model.users_changed.connect(self.render_users)
        self.view_model.selected_user_changed.connect(self.render_selected_user)
        self.view_model.messages_changed.connect(self.render_messages)

    @asyncSlot()
    async def load(self):
        await self.view_model.load_users()

    def render_users(self):
        self.user_list.clear()
        self._user_items.clear()

        return
        for user in self.view_model.users:
            item = QListWidgetItem(f"@{user.username}")

            self.user_list.addItem(item)

    def render_selected_user(self):
        user = self.view_model.selected_user

        if user is None:
            self.chat_panel.set_title("Select a user")
        else:
            self.chat_panel.set_title(f"DM with {user.username}")

    def render_messages(self):
        self.chat_panel.set_messages(self.view_model.messages)

    @asyncSlot(QListWidgetItem)
    async def on_user_clicked(self, item: QListWidgetItem):
        user_id = item.data(Qt.ItemDataRole.UserRole)
        user = self._user_items[user_id]

        await self.view_model.select_user(user)

    @asyncSlot(str)
    async def on_send_clicked(self, content: str):
        await self.view_model.send_message(content)
        self.chat_panel.clear_input()
