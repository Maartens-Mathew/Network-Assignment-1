from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from features.channels.repository.channel_repository import ChannelRepository
from features.chat.repository.chat_repository import ChatRepository
from features.channels.viewmodel.channel_viewmodel import ChannelsViewModel
from features.chat.viewmodel.channel_chat_viewmodel import ChannelChatViewModel

class ChannelContainer(DeclarativeContainer):
    network_container = providers.DependenciesContainer()

    channel_repository = providers.Singleton(
        ChannelRepository,
        client=network_container.chat_protocol,
    )

    chat_repository = providers.Singleton(
        ChatRepository,
        client=network_container.chat_protocol
    )

    channels_view_model = providers.Singleton(
        ChannelsViewModel,
        repository=channel_repository,
    )

    chat_view_model = providers.Singleton(
        ChannelChatViewModel,
        chat_repository=chat_repository
    )
