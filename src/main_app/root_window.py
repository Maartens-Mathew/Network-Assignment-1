from collections.abc import Callable

from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget
from qasync import asyncSlot

from features.chat.repository.chat_repository import ChatRepository
from main_app.viewmodel.app_viewmodel import AppViewModel
from features.auth.viewmodel.login_viewmodel import LoginViewModel
from features.channels.view.channel_screen import ChannelScreen
from features.auth.view.login_view import LoginScreen
from main_app.main_app_window import MainAppView
from features.users.view.user_screen import UserScreen


class RootWindow(QMainWindow):
    def __init__(
        self,
        chat_repository: ChatRepository,
        login_view_model: LoginViewModel,
        app_view_model: AppViewModel,
        login_screen_factory: Callable[[], LoginScreen],
        channel_screen_factory: Callable[[], ChannelScreen],
        user_screen_factory: Callable[[], UserScreen],
    ):
        super().__init__()

        self.setWindowTitle("PySide6 Chat Client")
        self.resize(1100, 700)

        self.repository = chat_repository
        self.login_view_model = login_view_model
        self.app_view_model = app_view_model

        self.login_screen = login_screen_factory()
        self.channels_screen = channel_screen_factory()
        self.users_screen = user_screen_factory()

        self.main_app_view = MainAppView(
            self.app_view_model,
            self.channels_screen,
            self.users_screen,
        )

        self.root_stack = QStackedWidget()
        self.root_stack.addWidget(self.login_screen)
        self.root_stack.addWidget(self.main_app_view)

        self.setCentralWidget(self.root_stack)

        self.login_view_model.login_succeeded.connect(self.on_login_successful)

    @asyncSlot()
    async def on_login_successful(self):
        self.root_stack.setCurrentWidget(self.main_app_view)

        try:
            await self.app_view_model.load_current_user()
            await self.channels_screen.load()
            await self.users_screen.load()
        except Exception as e:
            QMessageBox.warning(self, "Load Failed", str(e))
