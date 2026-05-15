from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from infrastructure.chat_protocol import create_udp_client, ChatProtocol


class NetworkContainer(DeclarativeContainer):
    """
    Dependency injection container for Network-related dependencies

    This container holds all the dependencies related to network functionality. It holds the network:
    - Chat Protocol
    - UDP Client
    - Server Configuration
    - (Eventually) WireguardSession Client

    Any further dependencies related specifically to network and lower layers should be added here.
    """


    config = providers.Configuration()

    create_chat_protocol = providers.Coroutine(
        create_udp_client,
        host=config.server.host,
        port=config.server.port,
    )
    chat_protocol = providers.Dependency(instance_of=ChatProtocol)