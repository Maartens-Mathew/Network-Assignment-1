from PySide6.QtCore import QObject, Signal, Property
from qasync import asyncSlot

from core.keystore.key_store import KeyStore
from main_app.repository.session_repository import SessionRepository


class LoginViewModel(QObject):
    fields_changed = Signal()
    can_continue_changed = Signal(bool)
    loading_changed = Signal(bool)
    login_failed = Signal(str)
    login_succeeded = Signal()

    def __init__(self, session_repository: SessionRepository):
        super().__init__()

        self._username = ""
        self._public_key = ""
        self._private_key = ""
        self._is_loading = False
        self.key_store = KeyStore(app_name="chat_client", password=b"csc4026z")
        self._session_repository = session_repository

    @Property(str, notify=fields_changed)
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if self._username == value:
            return
        self._username = value
        self.fields_changed.emit()

    @Property(str, notify=fields_changed)
    def public_key(self):
        return self._public_key

    @public_key.setter
    def public_key(self, value):
        if self._public_key == value:
            return
        self._public_key = value
        self.fields_changed.emit()

    @Property(str, notify=fields_changed)
    def private_key(self):
        return self._private_key

    @private_key.setter
    def private_key(self, value):
        if self._private_key == value:
            return
        self._private_key = value
        self.fields_changed.emit()

    @Property(bool, notify=fields_changed)
    def canContinue(self):
        return (
            bool(self._username.strip())
            and bool(self._public_key.strip())
            and bool(self._private_key.strip())
        )

    @Property(bool, notify=loading_changed)
    def isLoading(self):
        return self._is_loading

    @asyncSlot()
    async def confirm(self):
        """Call this when the login button is clicked."""
        if not self.canContinue:
            self.can_continue_changed.emit(False)
            return

        self._is_loading = True
        self.loading_changed.emit(True)
        try:
            self.key_store.save(
                username=self._username,
                private_key=self._private_key,
                public_key=self._public_key,
            )

            await self._session_repository.connect(
                username=self._username,
                private_key=self._private_key,
                public_key=self._public_key,
            )

            self.login_succeeded.emit()
        except Exception as e:
            self.login_failed.emit(str(e))
        finally:
            self._is_loading = False
            self.loading_changed.emit(False)

    @asyncSlot()
    async def login(self):
        await self.confirm()

    def clear(self):
        self._username = ""
        self._public_key = ""
        self._private_key = ""
        self.fields_changed.emit()
