"""
PROBE 25 — Wireguard Transport Counter Replay
Hypothesis: WireGuard transport messages include a counter to prevent replay
attacks. Does the server reject replayed packets?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import socket
import struct
import msgpack
from vulnerabilities.lib.probe import make_handle, report

async def run_async():
    priv_hex = os.environ.get('WG_STATIC_PRIVATE')
    pub_hex  = os.environ.get('WG_STATIC_PUBLIC')
    if not priv_hex or not pub_hex:
        print("Skipping — WG_STATIC_PRIVATE/PUBLIC not set. Run: source .env")
        report(
            'PROBE 25 — Wireguard Replay Attack',
            "Server rejects replayed transport packets (counter already seen)",
            'SKIPPED — no WG keys',
            False
        )
        return

    from encryption.session import WireguardSession
    from encryption.handshake import build_initiation, process_response
    from encryption.transport import wrap_message, unwrap_message
    from encryption.session import SERVER_STATIC_PUBLIC_KEY

    priv = bytes.fromhex(priv_hex)
    pub  = bytes.fromhex(pub_hex)

    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.connect(('csc4026z.link', 51820))

    # Complete handshake manually to get keys
    init_msg, eph_priv, ck, h, sidx, mac1 = build_initiation(priv, pub, SERVER_STATIC_PUBLIC_KEY)
    await loop.sock_sendall(sock, init_msg)
    response = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=10.0)

    if response[0] == 0x03:
        from encryption.handshake import process_cookie_reply
        cookie = process_cookie_reply(response, SERVER_STATIC_PUBLIC_KEY, mac1)
        init_msg, eph_priv, ck, h, sidx, mac1 = build_initiation(priv, pub, SERVER_STATIC_PUBLIC_KEY, cookie=cookie)
        await loop.sock_sendall(sock, init_msg)
        response = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=10.0)

    send_key, recv_key, recv_idx = process_response(response, eph_priv, priv, ck, h)
    print(f"Handshake complete. recv_idx={recv_idx}")

    # Build a CONNECT message
    connect_payload = msgpack.packb({'request_type': 1, 'request_handle': make_handle()})

    # Packet with counter=0
    packet_0 = wrap_message(connect_payload, send_key, 0, recv_idx)
    await loop.sock_sendall(sock, packet_0)
    r0 = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=5.0)
    print(f"Original packet (counter=0): response type={r0[0]}")

    # Replay the exact same packet
    await loop.sock_sendall(sock, packet_0)
    try:
        r_replay = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=3.0)
        print(f"Replayed packet (counter=0 again): got response type={r_replay[0]}")
        replay_accepted = True
    except asyncio.TimeoutError:
        print("Replayed packet: NO RESPONSE (server correctly ignored replay)")
        replay_accepted = False

    # Also try counter going backwards after sending a few more
    ping = msgpack.packb({'request_type': 3, 'request_handle': make_handle(), 'session': 0})
    for i in range(1, 4):
        pkt = wrap_message(ping, send_key, i, recv_idx)
        await loop.sock_sendall(sock, pkt)
        try:
            await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=2.0)
        except asyncio.TimeoutError:
            pass

    # Now replay counter=0 again (clearly old)
    await loop.sock_sendall(sock, packet_0)
    try:
        r_old = await asyncio.wait_for(loop.sock_recv(sock, 65535), timeout=2.0)
        print(f"Old counter=0 replay after counter=3: got response type={r_old[0]}")
        old_replay_accepted = True
    except asyncio.TimeoutError:
        print("Old counter=0 replay: NO RESPONSE (server correctly rejected)")
        old_replay_accepted = False

    sock.close()

    vulnerable = replay_accepted or old_replay_accepted
    report(
        'PROBE 25 — Wireguard Replay Attack',
        "Server accepts replayed WireGuard transport packets (counter reuse)",
        {'immediate_replay': replay_accepted, 'old_replay': old_replay_accepted},
        vulnerable,
        evidence=f"immediate_replay={replay_accepted}, old_replay={old_replay_accepted}"
    )


def run():
    asyncio.run(run_async())


if __name__ == '__main__':
    run()
