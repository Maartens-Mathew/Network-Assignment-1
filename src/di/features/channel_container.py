from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from features.channels.repository.channel_repository import ChannelRepository
from features.chat.repository.chat_repository import ChatRepository
from features.channels.viewmodel.channel_viewmodel import ChannelsViewModel
from features.channels.view.channel_screen import ChannelScreen
from features.chat.viewmodel.channel_chat_viewmodel import ChannelChatViewModel


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

    channel_repository = providers.Singleton(
        ChannelRepository,
        client=network_container.chat_protocol,
    )

    chat_repository = providers.Singleton(
        ChatRepository,
        client = network_container.chat_protocol
    )

    channels_view_model = providers.Singleton(
        ChannelsViewModel,
        repository=channel_repository,
    )

    chat_view_model = providers.Singleton(
        ChannelChatViewModel,
        chat_repository = chat_repository
    )

    channel_screen = providers.Factory(
        ChannelScreen,
        view_model=channels_view_model,
        chat_view_model = chat_view_model
    )