from dependency_injector import containers, providers

from features.auth.viewmodel.login_viewmodel import LoginViewModel

class LoginContainer(containers.DeclarativeContainer):
    container = providers.DependenciesContainer()

    login_view_model = providers.Singleton(
        LoginViewModel,
        session_repository=container.session_repository,
    )