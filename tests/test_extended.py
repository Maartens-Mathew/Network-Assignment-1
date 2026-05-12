"""
Extended live tests against csc4026z.link:51821 (mac2 / cookie challenge port).

The server on this port always responds to the first initiation with a Cookie
Reply (type 0x03). The client must decrypt the cookie and resend the initiation
with mac2 set before the server will complete the handshake.

Before running:
    source .env

Run with: uv run pytest tests/test_extended.py -v -s
"""

import asyncio
import os
import socket
import pytest
import msgpack
import random

from encryption.session import WireguardSession, SERVER_STATIC_PUBLIC_KEY
from encryption.handshake import build_initiation, process_response, process_cookie_reply
from encryption.transport import wrap_message, unwrap_message

SERVER_HOST     = 'csc4026z.link'
SERVER_PORT_EXT = 51821


def load_keys():
    priv_hex = os.environ.get('WG_STATIC_PRIVATE')
    pub_hex  = os.environ.get('WG_STATIC_PUBLIC')
    if not priv_hex or not pub_hex:
        pytest.skip("Run: source .env")
    return bytes.fromhex(priv_hex), bytes.fromhex(pub_hex)


async def make_extended_session():
    priv, pub = load_keys()
    session   = WireguardSession(priv, pub)
    await session.connect(SERVER_HOST, SERVER_PORT_EXT)
    return session


def make_request(session, request_type, **kwargs):
    handle = random.randrange(0, 2**32)
    msg = {
        'request_type':   request_type,
        'session':        session.chat_session,
        'request_handle': handle,
        **kwargs
    }
    return msgpack.packb(msg), handle


# ── Low-level cookie flow verification ───────────────────────────────────────

@pytest.mark.asyncio
async def test_server_sends_cookie_reply_on_first_initiation():
    """
    Explicitly verify the server's cookie challenge flow step by step:
      1. Send initiation with mac2 = 0 → server MUST respond with type 0x03
      2. Decrypt the cookie from the reply
      3. Resend initiation with mac2 set → server MUST respond with type 0x02
    This is the core proof that mac2 is implemented correctly.
    """
    priv, pub = load_keys()
    loop = asyncio.get_running_loop()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.connect((SERVER_HOST, SERVER_PORT_EXT))

    try:
        # Step 1: send initiation with mac2 = 0
        init_msg, eph_priv, ck, h, sidx, mac1 = build_initiation(
            priv, pub, SERVER_STATIC_PUBLIC_KEY
        )
        await loop.sock_sendall(sock, init_msg)

        # Step 2: server must reply with cookie reply (type 0x03)
        reply = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=10.0)
        assert reply[0] == 0x03, (
            f"Expected cookie reply (0x03) from port 51821, got {hex(reply[0])}"
        )
        assert len(reply) == 64, f"Cookie reply should be 64 bytes, got {len(reply)}"
        print(f"\nGot cookie reply (type=0x03, {len(reply)} bytes) — cookie challenge confirmed")

        # Step 3: decrypt the cookie and resend with mac2
        cookie = process_cookie_reply(reply, SERVER_STATIC_PUBLIC_KEY, mac1)
        assert len(cookie) == 16, f"Decrypted cookie should be 16 bytes, got {len(cookie)}"
        print(f"Cookie decrypted OK ({len(cookie)} bytes)")

        init_msg2, eph_priv2, ck2, h2, sidx2, mac1_2 = build_initiation(
            priv, pub, SERVER_STATIC_PUBLIC_KEY, cookie=cookie
        )
        await loop.sock_sendall(sock, init_msg2)

        # Step 4: server must now respond with handshake response (type 0x02)
        response = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=10.0)
        assert response[0] == 0x02, (
            f"Expected handshake response (0x02) after valid mac2, got {hex(response[0])}"
        )
        print(f"Got handshake response (type=0x02) — mac2 accepted by server")

        # Verify we can derive valid transport keys
        send_key, recv_key, recv_idx = process_response(response, eph_priv2, priv, ck2, h2)
        assert len(send_key) == 32
        assert len(recv_key) == 32
        print(f"Transport keys derived OK")

    finally:
        sock.close()


# ── Session-level tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extended_handshake_and_connect():
    """Full cookie-challenge handshake + CONNECT on port 51821."""
    session = await make_extended_session()
    assert session.chat_session is not None
    assert session.username is not None
    print(f"\nConnected (extended) as: {session.username}")
    await session.close()


@pytest.mark.asyncio
async def test_extended_ping():
    """Send a PING over the extended port and get a response."""
    session = await make_extended_session()

    ping, handle = make_request(session, 3)
    await session.send(ping)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 24
    assert response.get(b'response_handle') == handle
    print(f"\nPING response: {response}")
    await session.close()


@pytest.mark.asyncio
async def test_extended_whoami():
    """WHOAMI over extended port — username should match what connect returned."""
    session = await make_extended_session()

    whoami, handle = make_request(session, 11)
    await session.send(whoami)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 32
    assert response.get(b'username', b'').decode() == session.username
    print(f"\nWHOAMI (extended): {session.username}")
    await session.close()


@pytest.mark.asyncio
async def test_extended_counter_increments():
    """Send counter increments correctly over the extended port."""
    session = await make_extended_session()
    assert session.send_counter == 1  # CONNECT already sent

    for _ in range(3):
        ping, _ = make_request(session, 3)
        await session.send(ping)
        await asyncio.wait_for(session.receive(), timeout=5.0)

    assert session.send_counter == 4
    print(f"\nCounter after 3 pings (extended): {session.send_counter}")
    await session.close()


@pytest.mark.asyncio
async def test_extended_disconnect():
    """Clean disconnect from extended port."""
    session = await make_extended_session()
    await session.close()
    assert not session.connected
    print("\nClean disconnect (extended)")
