import asyncio
import random
import socket
import struct
import msgpack

from .handshake import build_initiation, process_response, process_cookie_reply
from .transport import wrap_message, unwrap_message

SERVER_STATIC_PUBLIC_KEY = b'f,^\xc0Cb\xf3\x937\xbf\x11\x14"\xed\x13\x0b\x9f\xe7\xaf;\x94\xb0p\x13\xe1\x94\xdd\x85\xcf\x01\x0bC'


class WireguardSession:
    """
    Encrypted UDP session using simplified Wireguard protocol.

    Usage:
        session = WireguardSession(static_private_key, static_public_key)
        await session.connect('csc4026z.link', 51820)

        await session.send(msgpack.packb({'request_type': 3, ...}))
        data = await session.receive()
        msg  = msgpack.unpackb(data)
    """

    PING_INTERVAL = 30  # seconds

    def __init__(self, static_private_key: bytes, static_public_key: bytes):
        self.static_priv = static_private_key
        self.static_pub  = static_public_key

        self.send_key       = None
        self.recv_key       = None
        self.send_counter   = 0
        self.recv_counter   = 0
        self.receiver_index = None   # server's sender index (I_r)
        self.sender_index   = None   # our sender index (I_i)

        self.chat_session = None
        self.username     = None

        self._host      = None
        self._port      = None
        self._sock      = None
        self._recv_queue = asyncio.Queue()
        self._recv_task  = None
        self._ping_task  = None
        self._connected  = False

        self._pending = {}

    async def connect(self, host: str, port: int):
        """Perform Wireguard handshake then send CONNECT chat message."""
        self._host = host
        self._port = port

        loop = asyncio.get_running_loop()

        # Create connected UDP socket (non-blocking)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.connect((host, port))

        # --- Wireguard handshake ---
        init_msg, ephemeral_priv, chain_key, hash_, sender_index, mac1 = build_initiation(
            self.static_priv, self.static_pub, SERVER_STATIC_PUBLIC_KEY
        )
        self.sender_index = sender_index

        # Send initiation packet.
        # NOTE: sock_sendall works for connected UDP on Linux (wraps send() once).
        # If this fails on your platform, replace with: self._sock.send(init_msg)
        await loop.sock_sendall(self._sock, init_msg)

        # Wait for handshake response — may be type 0x02 (done) or 0x03 (cookie challenge)
        response = await asyncio.wait_for(self._raw_recv(), timeout=10.0)

        if response[0] == 0x03:
            # Cookie reply: decrypt the cookie and resend initiation with mac2 set
            cookie = process_cookie_reply(response, SERVER_STATIC_PUBLIC_KEY, mac1)
            init_msg, ephemeral_priv, chain_key, hash_, sender_index, mac1 = build_initiation(
                self.static_priv, self.static_pub, SERVER_STATIC_PUBLIC_KEY, cookie=cookie
            )
            self.sender_index = sender_index
            await loop.sock_sendall(self._sock, init_msg)
            response = await asyncio.wait_for(self._raw_recv(), timeout=10.0)

        if response[0] != 0x02:
            raise ConnectionError(f"Expected handshake response (0x02), got {hex(response[0])}")

        self.send_key, self.recv_key, self.receiver_index = process_response(
            response, ephemeral_priv, self.static_priv, chain_key, hash_
        )
        self.send_counter = 0
        self.recv_counter = 0

        # Start background receive loop
        self._recv_task = asyncio.create_task(self._receive_loop())

        # --- Chat CONNECT (request_type 1) ---
        handle = random.randrange(0, 2**32)
        connect_msg = msgpack.packb({
            'request_type': 1,
            'request_handle': handle
        })
        await self.send(connect_msg)

        # Wait for CONNECT response
        response_data = await asyncio.wait_for(self._recv_queue.get(), timeout=10.0)
        parsed = msgpack.unpackb(response_data, raw=True)

        if parsed.get(b'response_type') == 20:  # ERROR
            raise ConnectionError(f"Server error: {parsed.get(b'error')}")

        self.chat_session = parsed[b'session']
        self.username     = parsed.get(b'username', b'').decode()

        self._ping_task = asyncio.create_task(self._ping_loop())
        self._connected = True

    async def send(self, plaintext_bytes: bytes):
        """Encrypt and send a msgpack message."""
        loop = asyncio.get_running_loop()
        packet = wrap_message(
            plaintext_bytes,
            self.send_key,
            self.send_counter,
            self.receiver_index
        )
        self.send_counter += 1
        # NOTE: sock_sendall on a connected non-blocking UDP socket calls send() once.
        # Adjust to self._sock.send(packet) if sock_sendall behaves unexpectedly for UDP.
        await loop.sock_sendall(self._sock, packet)

    async def receive(self) -> bytes:
        """Return the next decrypted msgpack message from the server."""
        return await self._recv_queue.get()

    async def _raw_recv(self) -> bytes:
        """Read one raw UDP packet from the socket."""
        loop = asyncio.get_running_loop()
        return await loop.sock_recv(self._sock, 65535)

    async def _receive_loop(self):
        """Background task: read, decrypt, and queue incoming packets."""
        while True:
            try:
                raw = await self._raw_recv()
                if not raw:
                    continue

                if raw[0] == 0x04:
                    plaintext = unwrap_message(raw, self.recv_key, self.recv_counter)
                    self.recv_counter += 1
                    await self._recv_queue.put(plaintext)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[recv_loop error] {e}")

    async def _ping_loop(self):
        """Background task: send PING every 30 seconds to keep the session alive."""
        while True:
            try:
                await asyncio.sleep(self.PING_INTERVAL)
                if self.chat_session:
                    handle = random.randrange(0, 2**32)
                    ping = msgpack.packb({
                        'request_type': 3,
                        'session': self.chat_session,
                        'request_handle': handle
                    })
                    await self.send(ping)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ping_loop error] {e}")

    async def close(self):
        """Send DISCONNECT and clean up."""
        if self._ping_task:
            self._ping_task.cancel()
        if self._recv_task:
            self._recv_task.cancel()

        if self.chat_session:
            try:
                disconnect = msgpack.packb({
                    'request_type': 2,
                    'session': self.chat_session,
                    'request_handle': random.randrange(0, 2**32)
                })
                await self.send(disconnect)
            except Exception:
                pass

        if self._sock:
            self._sock.close()

        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected
