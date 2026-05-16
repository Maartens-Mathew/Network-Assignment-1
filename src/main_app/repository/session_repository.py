from core.requests import ConnectRequest
from core.responses.session.connect import ConnectResponse
from core.types import ResponseType
from network_client.chat_protocol import ChatProtocol


class SessionRepository:
    def __init__(self, client: ChatProtocol):
        self._client = client

    async def connect(
        self,
        username: str,
        public_key: str,
        private_key: str,
    ) -> dict:
        response : ConnectResponse = await self._client.send_request(ConnectRequest())
        response_type = response.response_type

        if response_type == ResponseType.ERROR:
            error = response.get("error") or response.get(b"error") or "Connection failed."
            if isinstance(error, bytes):
                error = error.decode(errors="replace")
            raise ConnectionError(error)

        session = response.session

        if session is None:
            raise ConnectionError("Connection failed: server did not return a session.")

        self._client.session = int(session)

        return response.to_dict()
