from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from repositories.session_repository import SessionRepository


class SessionContainer(DeclarativeContainer):
    """
    Dependency injection container for Session-related dependencies

    This container holds all the dependencies related to session functionality. It holds the session:
    - Session Repository

    Any further dependencies related specifically to session should be added here.

    NOTE: It's unclear whether there is a need specifically for this container (since session is
    managed at the lower, network level). It's kept here for now for completeness.
    """

    container = providers.DependenciesContainer()

    session_repository = providers.Singleton(
        SessionRepository,
        client=container.chat_protocol,
    )