from PySide6.QtCore import QObject, Signal

from core.keystore.key_store import KeyStore
from main_app.model.app_section import AppSection
from features.users.model.user import User
from features.chat.repository.chat_repository import ChatRepository
from features.users.repository.user_repository import UserRepository


class AppViewModel(QObject):
    current_section_changed = Signal()
    current_user_changed = Signal()
    key_values_show = Signal(dict)

    def __init__(self, user_repository : UserRepository):
        super().__init__()

        self.current_section = AppSection.CHANNELS
        self.current_user: User | None = None

    async def change_username(self, username : str):
        pass


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