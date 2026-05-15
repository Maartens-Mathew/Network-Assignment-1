# infrastructure/chat_protocol.py
import asyncio
import random
from typing import TypeVar

import msgpack

from core.requests.request import Request
from core.responses.error import ErrorResponse
from core.responses.response import Response

R = TypeVar("R", bound=Response)


class ChatProtocol(asyncio.DatagramProtocol):
    """
    Owns the UDP socket and pending request map.
    Stores session token and injects it into every outgoing request.
    Repositories never handle session directly.
    """

    def __init__(self):
        self._transport: asyncio.DatagramTransport = None
        self._pending: dict[int, asyncio.Future[dict]] = {}
        self._session: int | None = None

    # -------------------------
    # Session
    # -------------------------

    @property
    def session(self) -> int | None:
        return self._session

    @session.setter
    def session(self, value: int) -> None:
        self._session = value

    # -------------------------
    # asyncio.DatagramProtocol
    # -------------------------

    def connection_made(self, transport: asyncio.DatagramTransport):
        self._transport = transport

    def datagram_received(self, data: bytes, addr):
        response = msgpack.unpackb(data, raw=False)
        print(f"Received: {response}")
        handle = (
            response.get("request_handle")
            or response.get("response_handle")
            or response.get(b"request_handle")
            or response.get(b"response_handle")
        )

        if handle in self._pending:
            future = self._pending.pop(handle)
            if not future.done():
                future.set_result(response)

    def error_received(self, exc: Exception):
        self._fail_all(exc)

    def connection_lost(self, exc):
        self._fail_all(exc or ConnectionError("Socket closed"))

    # -------------------------
    # Public API
    # -------------------------

    async def send_request(self, request: Request[R], timeout: float = 5.0) -> R | ErrorResponse:
        request.request_handle = random.randint(0, 2**32 - 1)
        request.session = self._session or 0

        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        self._pending[request.request_handle] = future

        self._transport.sendto(msgpack.packb(request.to_dict()))

        try:
            raw = await asyncio.wait_for(future, timeout=timeout)
            return request.deserialize(raw)  # R is resolved here
        except asyncio.TimeoutError:
            await self._pending.pop(request.request_handle, None)
            raise

    # -------------------------
    # Internal
    # -------------------------

    def _fail_all(self, exc: Exception):
        for future in self._pending.values():
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()


async def create_udp_client(host: str, port: int) -> ChatProtocol:
    loop = asyncio.get_event_loop()
    _, protocol = await loop.create_datagram_endpoint(
        ChatProtocol,
        remote_addr=(host, port)
    )
    return protocol