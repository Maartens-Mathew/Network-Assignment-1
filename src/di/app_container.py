from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from main_app.viewmodel.app_viewmodel import AppViewModel
from main_app.root_window import RootWindow



class AppContainer(DeclarativeContainer):
    """
    Dependency injection container for app-level (across the whole application).

    This container holds everything that will exist for the entire duration of the app while
    it's running.
    """

    container = providers.DependenciesContainer()

    app_view_model = providers.Singleton(
        AppViewModel,
        user_repository= container.user_repository
    )

    root_window = providers.Factory(
        RootWindow,
        chat_repository=container.chat_repository,
        login_view_model= container.login_view_model,
        app_view_model=app_view_model,
        channel_screen_factory=container.channel_screen.provider,
        user_screen_factory=container.user_screen.provider,
        login_screen_factory=container.login_screen.provider
    )