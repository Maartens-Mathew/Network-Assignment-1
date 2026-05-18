import os
import sys
from dependency_injector import providers
from qasync import QEventLoop
import asyncio

base_dir = os.path.join(os.getcwd(), "src")
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from di.app_container import AppContainer
from di.features.login_container import LoginContainer
from di.features.channel_container import ChannelContainer
from di.session_container import SessionContainer
from di.features.user_container import UserContainer
from di.network_container import NetworkContainer

network_container = NetworkContainer()
network_container.config.server.host.from_value("csc4026z.link")
network_container.config.server.port.from_value(51825)

channel_container = ChannelContainer()
session_container = SessionContainer()
login_container = LoginContainer()
user_container = UserContainer()
app_container = AppContainer()

from PySide6.QtWidgets import QApplication

app = QApplication([])
loop = QEventLoop(app)
asyncio.set_event_loop(loop)
chat_protocol = loop.run_until_complete(network_container.create_chat_protocol())
network_container.chat_protocol.override(providers.Object(chat_protocol))

channel_container.network_container.override(network_container)
session_container.container.override(network_container)
user_container.container.override(providers.DependenciesContainer(chat_protocol=network_container.chat_protocol))
login_container.container.override(providers.DependenciesContainer(session_repository=session_container.session_repository, app_view_model=app_container.app_view_model))
app_container.container.override(providers.DependenciesContainer(chat_repository=channel_container.chat_repository, user_repository=user_container.user_repository, login_view_model=login_container.login_view_model))

print('app_view_model', app_container.app_view_model())
print('login_view_model', login_container.login_view_model())
print('channels_view_model', channel_container.channels_view_model())
print('users_view_model', user_container.users_view_model())
