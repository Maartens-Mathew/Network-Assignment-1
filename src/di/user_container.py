from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from repositories.user_repository import UserRepository
from viewmodels.user_viewmodel import UsersViewModel
from views.user_screen.user_screen import UserScreen


class UserContainer(DeclarativeContainer):
    """
    Dependency injection container for User-related dependencies

    This container holds all the dependencies related to user functionality. It holds the user:
    - User Repository
    - User View Model
    - User Screen

    Any further dependencies related specifically to user should be added here.
    """

    container = providers.DependenciesContainer()

    user_repository = providers.Singleton(
        UserRepository,
        client=container.chat_protocol,
    )

    users_view_model = providers.Singleton(
        UsersViewModel,
        repository=user_repository,
    )

    user_screen = providers.Factory(
        UserScreen,
        view_model=users_view_model,
    )