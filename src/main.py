import asyncio
import os
import sys

# Ensure `src` directory is on sys.path so top-level imports like `di` work
# when running with `python -m src.main` from the workspace root.
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from dependency_injector import providers
from qasync import QEventLoop, asyncSlot

from di.app_container import AppContainer
from di.network_container import NetworkContainer
from di.features.channel_container import ChannelContainer
from di.features.login_container import LoginContainer
from di.session_container import SessionContainer
from di.features.user_container import UserContainer
# No direct QWidget imports when running QML UI


def main() -> None:
    # 1. Initialize the QML-friendly Application Context
    app = QGuiApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 2. Build backend DI graph exactly as before
    network_container = NetworkContainer()
    network_container.config.server.host.from_value("csc4026z.link")
    network_container.config.server.port.from_value(51825)

    channel_container = ChannelContainer()
    session_container = SessionContainer()
    login_container = LoginContainer()
    user_container = UserContainer()
    app_container = AppContainer()

    with loop:
        chat_protocol = loop.run_until_complete(
            network_container.create_chat_protocol()
        )

        network_container.chat_protocol.override(
            providers.Object(chat_protocol)
        )

        channel_container.network_container.override(network_container)
        session_container.container.override(network_container)

        user_container.container.override(
            providers.DependenciesContainer(
                chat_protocol=network_container.chat_protocol,
            )
        )

        login_container.container.override(
            providers.DependenciesContainer(
                session_repository=session_container.session_repository,
                app_view_model=app_container.app_view_model,
            )
        )

        app_container.container.override(
            providers.DependenciesContainer(
                chat_repository=channel_container.chat_repository,
                user_repository=user_container.user_repository,
                login_view_model=login_container.login_view_model
            )
        )

        # Initialize the app lifecycle synchronization manager
        channels_vm = channel_container.channels_view_model()
        users_vm = user_container.users_view_model()
        app_vm = app_container.app_view_model()
        login_vm = login_container.login_view_model()

        lifecycle_manager = AppLifecycleManager(
            channels_vm,
            users_vm
        )

        # 3. Instantiate QML Engine
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda warnings: [print(f"❌ QML Error: {w.toString()}") for w in warnings])
        context = engine.rootContext()

        # 4. Bridge All resolved ViewModels directly as global variables for QML components
        context.setContextProperty("appViewModel", app_vm)
        context.setContextProperty("loginViewModel", login_vm)
        context.setContextProperty("channelsViewModel", channels_vm)
        context.setContextProperty("usersViewModel", users_vm)
        context.setContextProperty("appInitializer", lifecycle_manager)

        # 5. DIAGNOSTIC HOOK: Catches compilation or missing import errors in your QML files
        def handle_object_created(obj, url):
            if not obj:
                print(f"\n❌ QML Error: Engine failed to compile or load: {url.toLocalFile()}")
                print(
                    "Review the terminal log messages immediately above this error for line-by-line syntax details.\n")

        engine.objectCreated.connect(handle_object_created)

        # 6. Bulletproof Absolute File Path Resolution
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qml_path = os.path.join(base_dir, "main_app", "RootWindow.qml")

        # Load the file safely wrapped as a Local File URL
        engine.load(QUrl.fromLocalFile(qml_path))

        # Check if root object failed to instantiate
        if not engine.rootObjects():
            sys.exit(-1)

        # 7. Start the main event loop cleanly (Fixed nested scope bug)
        loop.run_forever()


class AppLifecycleManager(QObject):
    """Manages structural background data tasks after successful authentication."""
    initializationFailed = Signal(str)

    def __init__(self, channel_vm, user_vm):
        super().__init__()
        self.channel_vm = channel_vm
        self.user_vm = user_vm

    @Slot()
    @asyncSlot()
    async def initialize_authenticated_session(self):
        try:
            # Concurrent async tasks triggered safely on the event loop
            await asyncio.gather(
                self.channel_vm.load_channels(),
                self.user_vm.load_users()  # Assuming user viewmodel has a matching loading routine
            )
        except Exception as e:
            self.initializationFailed.emit(str(e))


if __name__ == "__main__":
    main()