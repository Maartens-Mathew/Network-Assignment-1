from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from infrastructure import chat_protocol
from repositories.channel_repository import ChannelRepository
from repositories.chat_repository import ChatRepository
from viewmodels.channel_viewmodel import ChannelsViewModel
from views.channel_screen.channel_screen import ChannelScreen


class ChannelContainer(DeclarativeContainer):
    """
    Dependency injection container for Channels

    This container holds all the dependencies related to channels. It holds the chat:
    - Repository
    - View Model
    - Screen

    Any further dependencies related specifically to channels should be added here.
    """

    network_container = providers.DependenciesContainer()

    chat_repository = providers.Singleton(ChatRepository)
    channel_repository = providers.Singleton(
        ChannelRepository,
        client=network_container.chat_protocol,
    )

    channels_view_model = providers.Singleton(
        ChannelsViewModel,
        repository=channel_repository,
    )

    channel_screen = providers.Factory(
        ChannelScreen,
        view_model=channels_view_model,
    )