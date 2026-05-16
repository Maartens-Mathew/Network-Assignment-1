from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from features.auth.viewmodel.login_viewmodel import LoginViewModel
from main_app.viewmodel.app_viewmodel import AppViewModel


class LoginScreen(QWidget):
    def __init__(
            self,
            login_view_model: LoginViewModel,
            app_view_model: AppViewModel
    ):
        super().__init__()

        self.login_view_model = login_view_model
        self.app_view_model = app_view_model

        # Widgets
        self.title = QLabel("Chat Client Login")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setObjectName("LoginTitle")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setText("Mathew")


        self.public_key_input = QLineEdit()
        self.public_key_input.setPlaceholderText("Public Key")
        self.public_key_input.setText("ZixewENi85M3vxEUIu0TC5/nrzuUsHAT4ZTdhc8BC0M=")

        self.private_key_input = QLineEdit()
        self.private_key_input.setPlaceholderText("Private Key")
        self.private_key_input.setText("WdNR7FDQb4Flb2IBV7Y6/V20cTZ+XwynszMbxaeiCjE=")

        self.login_button = QPushButton("Login")

        # Layout
        login_card = self._build_card()
        outer_layout = QVBoxLayout()
        outer_layout.addStretch()
        outer_layout.addWidget(login_card, alignment=Qt.AlignmentFlag.AlignCenter)
        outer_layout.addStretch()
        self.setLayout(outer_layout)

        # Connections — inputs update the view model
        self.username_input.textChanged.connect(lambda v: setattr(self.login_view_model, "username", v))
        self.public_key_input.textChanged.connect(lambda v: setattr(self.login_view_model, "public_key", v))
        self.private_key_input.textChanged.connect(lambda v: setattr(self.login_view_model, "private_key", v))

        self.login_button.clicked.connect(self._on_login_clicked)

        self.login_view_model.username = self.username_input.text()
        self.login_view_model.public_key = self.public_key_input.text()
        self.login_view_model.private_key = self.private_key_input.text()

        # Connections — view model updates the UI
        self.login_view_model.fields_changed.connect(self._on_fields_changed)
        self.login_view_model.loading_changed.connect(self._on_loading_changed)
        self.login_view_model.login_failed.connect(self._on_login_failed)
        self.login_view_model.login_succeeded.connect(self._on_login_succeeded)

    def _build_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("LoginCard")

        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.addWidget(self.title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.public_key_input)
        layout.addWidget(self.private_key_input)
        layout.addWidget(self.login_button)

        card.setLayout(layout)
        return card

    def _on_login_succeeded(self):
        self.app_view_model.go_to_channels()

    def _on_fields_changed(self):
        self.login_button.setEnabled(self.login_view_model.can_continue)

    def _on_loading_changed(self, is_loading: bool):
        self.login_button.setDisabled(is_loading)
        self.login_button.setText("Logging in..." if is_loading else "Login")

    def _on_login_failed(self, message: str):
        QMessageBox.warning(self, "Login Failed", message)

    @asyncSlot(bool)
    async def _on_login_clicked(self, checked: bool = False):
        await self.login_view_model.confirm()
