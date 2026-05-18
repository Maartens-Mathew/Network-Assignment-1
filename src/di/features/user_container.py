from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from features.users.repository.user_repository import UserRepository
from features.users.viewmodel.user_viewmodel import UsersViewModel


class UserContainer(DeclarativeContainer):
    container = providers.DependenciesContainer()

    user_repository = providers.Singleton(
        UserRepository,
        client=container.chat_protocol,
    )

    users_view_model = providers.Singleton(
        UsersViewModel,
        user_repository=user_repository,
    )
