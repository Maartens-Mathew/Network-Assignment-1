from dependency_injector import containers, providers

from features.auth.viewmodel.login_viewmodel import LoginViewModel
from features.auth.view.login_view import LoginScreen


class LoginContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for Login-related dependencies

    This container holds all the dependencies related to login functionality. It holds the login:
    - View Model
    - Screen

    Any further dependencies related specifically to login should be added here. Note that the name
    "login" will probably change, but login is fine for now because the user is logging on with their
    public and private keys.
    """

    container = providers.DependenciesContainer()


    login_view_model = providers.Singleton(
        LoginViewModel,
        session_repository=container.session_repository,
    )



    login_screen = providers.Factory(
        LoginScreen,
        login_view_model=login_view_model,
        app_view_model=container.app_view_model,
    )
