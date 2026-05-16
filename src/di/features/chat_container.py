from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from features.chat.repository.chat_repository import ChatRepository


class ChatContainer(DeclarativeContainer):
    """
    Dependency injection container for Chat-related dependencies

    This container holds all the dependencies related to chat functionality. It holds the chat:
    - Repository
    - View Model
    - Screen

    Any further dependencies related specifically to chat should be added here.
    """

    container = providers.DependenciesContainer()

    chat_repository = providers.Singleton(
        ChatRepository
    )