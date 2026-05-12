"""
Live integration tests against csc4026z.link:51820

Before running:
    source .env   # sets WG_STATIC_PRIVATE and WG_STATIC_PUBLIC

Run with: uv run pytest tests/test_live.py -v -s
"""

import asyncio
import os
import pytest
import msgpack
import random

from encryption.session import WireguardSession

SERVER_HOST = 'csc4026z.link'
SERVER_PORT = 51820

# ── Key loading ───────────────────────────────────────────────────────────────

def load_keys():
    """Load student keys from environment variables or skip."""
    priv_hex = os.environ.get('WG_STATIC_PRIVATE')
    pub_hex  = os.environ.get('WG_STATIC_PUBLIC')

    if not priv_hex or not pub_hex:
        pytest.skip(
            "Set WG_STATIC_PRIVATE and WG_STATIC_PUBLIC environment variables. "
            "Run: source .env"
        )

    return bytes.fromhex(priv_hex), bytes.fromhex(pub_hex)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def make_session():
    priv, pub = load_keys()
    session   = WireguardSession(priv, pub)
    await session.connect(SERVER_HOST, SERVER_PORT)
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


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_live_handshake_and_connect():
    """Full handshake + CONNECT: verifies Wireguard crypto works end-to-end."""
    session = await make_session()
    assert session.chat_session is not None
    assert session.username is not None
    print(f"\nConnected as: {session.username}")
    await session.close()


@pytest.mark.asyncio
async def test_live_ping():
    """Send a PING and get a response."""
    session = await make_session()

    ping, handle = make_request(session, 3)
    await session.send(ping)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 24
    assert response.get(b'response_handle') == handle
    print(f"\nPING response: {response}")
    await session.close()


@pytest.mark.asyncio
async def test_live_whoami():
    """Send WHOAMI and verify username matches what we got at connect."""
    session = await make_session()

    whoami, handle = make_request(session, 11)
    await session.send(whoami)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 32
    username = response.get(b'username', b'').decode()
    assert username == session.username
    print(f"\nWHOAMI: {username}")
    await session.close()


@pytest.mark.asyncio
async def test_live_channel_list():
    """Fetch the channel list."""
    session = await make_session()

    req, handle = make_request(session, 5)
    await session.send(req)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 26
    channels = response.get(b'channels', [])
    print(f"\nChannels: {[c.decode() for c in channels]}")
    await session.close()


@pytest.mark.asyncio
async def test_live_user_list():
    """Fetch the user list."""
    session = await make_session()

    req, handle = make_request(session, 14)
    await session.send(req)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 35
    users = response.get(b'users', [])
    print(f"\nUsers online: {[u.decode() for u in users]}")
    await session.close()


@pytest.mark.asyncio
async def test_live_set_username():
    """Change username and verify."""
    session  = await make_session()
    new_name = f"wg-test-{random.randint(1000, 9999)}"

    req, handle = make_request(session, 13, username=new_name)
    await session.send(req)

    response_data = await asyncio.wait_for(session.receive(), timeout=5.0)
    response      = msgpack.unpackb(response_data, raw=True)

    assert response.get(b'response_type') == 34
    print(f"\nUsername changed: {response.get(b'old_username')} -> {response.get(b'new_username')}")
    await session.close()


@pytest.mark.asyncio
async def test_live_counter_increments():
    """Verify send counter increments correctly across multiple messages."""
    session = await make_session()

    assert session.send_counter == 1  # CONNECT was already sent

    for i in range(3):
        ping, _ = make_request(session, 3)
        await session.send(ping)
        await asyncio.wait_for(session.receive(), timeout=5.0)

    assert session.send_counter == 4
    print(f"\nCounter after 3 pings: {session.send_counter}")
    await session.close()


@pytest.mark.asyncio
async def test_live_disconnect():
    """Send DISCONNECT and verify clean shutdown."""
    session = await make_session()
    await session.close()
    assert not session.connected
    print("\nClean disconnect")
