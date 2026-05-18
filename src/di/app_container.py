from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from main_app.viewmodel.app_viewmodel import AppViewModel

class AppContainer(DeclarativeContainer):
    container = providers.DependenciesContainer()

    # Still provides the shared application state manager
    app_view_model = providers.Singleton(
        AppViewModel,
        user_repository=container.user_repository
    )
