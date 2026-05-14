from dependency_injector import containers, providers

from infrastructure.chat_protocol import ChatProtocol, create_udp_client
from repositories.channel_repository import ChannelRepository
from repositories.chat_repository import ChatRepository
from repositories.session_repository import SessionRepository
from viewmodels.app_viewmodel import AppViewModel
from viewmodels.channel_viewmodel import ChannelsViewModel
from viewmodels.login_viewmodel import LoginViewModel
from viewmodels.user_viewmodel import UsersViewModel
from views.channel_screen.channel_screen import ChannelScreen
from views.login_screen.login_view import LoginScreen
from views.root_window import RootWindow
from views.user_screen.user_screen import UserScreen


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    create_chat_protocol = providers.Coroutine(
        create_udp_client,
        host=config.server.host,
        port=config.server.port,
    )
    chat_protocol = providers.Dependency(instance_of=ChatProtocol)

    chat_repository = providers.Singleton(ChatRepository)
    channel_repository = providers.Singleton(
        ChannelRepository,
        client=chat_protocol,
    )
    session_repository = providers.Singleton(
        SessionRepository,
        client=chat_protocol,
    )

    login_view_model = providers.Singleton(
        LoginViewModel,
        session_repository=session_repository,
    )
    app_view_model = providers.Singleton(
        AppViewModel,
        repository=chat_repository,
    )
    users_view_model = providers.Singleton(
        UsersViewModel,
        repository=chat_repository,
    )
    channels_view_model = providers.Singleton(
        ChannelsViewModel,
        repository=channel_repository,
    )

    channel_screen = providers.Factory(
        ChannelScreen,
        view_model=channels_view_model,
    )
    user_screen = providers.Factory(
        UserScreen,
        view_model=users_view_model,
    )

    login_screen = providers.Factory(
        LoginScreen,
        login_view_model=login_view_model,
        app_view_model=app_view_model,
    )

    root_window = providers.Factory(
        RootWindow,
        chat_repository=chat_repository,
        login_view_model=login_view_model,
        app_view_model=app_view_model,
        channel_screen_factory=channel_screen.provider,
        user_screen_factory=user_screen.provider,
        login_screen_factory=login_screen.provider
    )
