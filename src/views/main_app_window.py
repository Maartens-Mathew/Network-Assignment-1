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

from models.app_section import AppSection
from viewmodels.app_viewmodel import AppViewModel
from views.channel_screen.channel_screen import ChannelScreen
from views.user_screen.user_screen import UserScreen


class MainAppView(QWidget):
    def __init__(
        self,
        app_view_model: AppViewModel,
        channels_screen: ChannelScreen,
        users_screen: UserScreen,
    ):
        super().__init__()

        self.app_view_model = app_view_model
        self.channels_screen = channels_screen
        self.users_screen = users_screen

        self.channel_nav_button = QPushButton("Channels")
        self.user_nav_button = QPushButton("Users")

        self.channel_nav_button.setObjectName("NavButton")
        self.user_nav_button.setObjectName("NavButton")

        nav_bar = QFrame()
        nav_bar.setObjectName("NavBar")

        nav_layout = QVBoxLayout()
        nav_layout.addWidget(self.channel_nav_button)
        nav_layout.addWidget(self.user_nav_button)
        nav_layout.addStretch()

        nav_bar.setLayout(nav_layout)

        self.settings_button = QPushButton("Settings ▾")
        self.settings_button.setObjectName("SettingsButton")

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")

        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.settings_button)

        top_bar.setLayout(top_bar_layout)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.channels_screen)
        self.content_stack.addWidget(self.users_screen)

        content_area = QVBoxLayout()
        content_area.addWidget(top_bar)
        content_area.addWidget(self.content_stack)

        root_layout = QHBoxLayout()
        root_layout.addWidget(nav_bar)
        root_layout.addLayout(content_area)

        self.setLayout(root_layout)

        self.app_view_model.key_values_show.connect(self.show_current_keys)

        self.channel_nav_button.clicked.connect(self.app_view_model.go_to_channels)
        self.user_nav_button.clicked.connect(self.app_view_model.go_to_users)

        self.settings_button.clicked.connect(self.show_settings_menu)

        self.app_view_model.current_section_changed.connect(self.render_current_section)

        self.render_current_section()

    def show_current_keys(self, entries: dict):
        QMessageBox.information(
            self,
            "Key Values",
            f"Username: {entries['username']}\n\n"
            f"Public Key:\n{entries['public_key']}\n\n"
            f"Private Key:\n{entries['private_key']}",
        )


    def render_current_section(self):
        if self.app_view_model.current_section == AppSection.CHANNELS:
            self.content_stack.setCurrentWidget(self.channels_screen)
        elif self.app_view_model.current_section == AppSection.USERS:
            self.content_stack.setCurrentWidget(self.users_screen)

    def show_settings_menu(self):
        menu = QMenu(self)

        who_am_i_action = QAction("Who am I?", self)
        who_am_i_action.triggered.connect(self.show_current_user)

        key_values = QAction("Key Values", self)
        key_values.triggered.connect(self.app_view_model.get_entries)

        menu.addAction(who_am_i_action)
        menu.addAction(key_values)

        menu.exec(
            self.settings_button.mapToGlobal(
                self.settings_button.rect().bottomLeft()
            )
        )

    def show_current_user(self):
        user = self.app_view_model.current_user

        if user is None:
            QMessageBox.information(
                self,
                "Who am I?",
                "No user is currently loaded.",
            )
            return

        QMessageBox.information(
            self,
            "Who am I?",
            f"Username: @{user.username}\n"
        )
