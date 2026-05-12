"""
Shared probe helper.
Connects to the cleartext server (port 51825) unless told otherwise.
All probes use this for consistent connection handling.
"""

import socket
import msgpack
import random
import time
from typing import Optional, Any

SERVER_HOST = 'csc4026z.link'
CLEAR_PORT  = 51825
WG_PORT     = 51820


def make_handle() -> int:
    return random.randrange(1, 2**32)


def connect_cleartext() -> tuple:
    """
    Connect to cleartext server, return (sock, session_id, username).
    Performs CONNECT handshake automatically.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    sock.connect((SERVER_HOST, CLEAR_PORT))

    handle = make_handle()
    sock.send(msgpack.packb({'request_type': 1, 'request_handle': handle}))

    data = sock.recv(4096)
    response = msgpack.unpackb(data, raw=True)

    session  = response[b'session']
    username = response.get(b'username', b'').decode()
    return sock, session, username


def send_recv(sock: socket.socket, msg: dict, timeout: float = 5.0) -> Optional[dict]:
    """Send a msgpack message and return the parsed response."""
    sock.settimeout(timeout)
    try:
        sock.send(msgpack.packb(msg))
        data = sock.recv(4096)
        return msgpack.unpackb(data, raw=True)
    except socket.timeout:
        return None
    except Exception as e:
        return {b'error': str(e).encode()}


def send_raw(sock: socket.socket, raw_bytes: bytes) -> Optional[dict]:
    """Send raw bytes (not msgpack encoded) and return parsed response."""
    sock.settimeout(5.0)
    try:
        sock.send(raw_bytes)
        data = sock.recv(4096)
        return msgpack.unpackb(data, raw=True)
    except socket.timeout:
        return None
    except Exception as e:
        return {b'error': str(e).encode()}


def recv_all(sock: socket.socket, count: int, timeout: float = 3.0) -> list:
    """Receive up to `count` messages with timeout."""
    messages = []
    sock.settimeout(timeout)
    for _ in range(count):
        try:
            data = sock.recv(4096)
            messages.append(msgpack.unpackb(data, raw=True))
        except socket.timeout:
            break
    return messages


def report(probe_name: str, description: str, result: Any,
           vulnerable: bool, evidence: str = ''):
    """Standardised output for each probe."""
    status = 'VULNERABLE' if vulnerable else 'NOT VULNERABLE'
    print(f"\n{'='*60}")
    print(f"PROBE: {probe_name}")
    print(f"STATUS: {status}")
    print(f"DESCRIPTION: {description}")
    print(f"RESULT: {result}")
    if evidence:
        print(f"EVIDENCE: {evidence}")
    print('='*60)
    return vulnerable
