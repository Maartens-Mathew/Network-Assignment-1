"""
PROBE 24 — Reconnect with Same Wireguard Key / Multiple Sessions
Hypothesis: The server only allows a single connection per student (per static
key). What happens if you initiate a second WG handshake while the first is
still active? Tests general session uniqueness on cleartext first.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    # Test 1: Two simultaneous cleartext sessions from same IP
    sock1, session1, username1 = connect_cleartext()
    sock2, session2, username2 = connect_cleartext()
    print(f"Session 1: {session1}, username: {username1}")
    print(f"Session 2: {session2}, username: {username2}")
    assert session1 != session2, "Sessions must be different"

    r1 = send_recv(sock1, {'request_type': 3, 'session': session1, 'request_handle': make_handle()})
    r2 = send_recv(sock2, {'request_type': 3, 'session': session2, 'request_handle': make_handle()})
    print(f"Session 1 PING: {r1}")
    print(f"Session 2 PING: {r2}")
    both_active = (
        r1 and r1.get(b'response_type') == 24 and
        r2 and r2.get(b'response_type') == 24
    )
    print(f"Both sessions simultaneously active: {both_active}")
    sock1.close()
    sock2.close()

    # Test 2: Wireguard single-session enforcement (requires WG implementation)
    print("\nFor Wireguard single-session enforcement:")
    print("  The spec says only one connection per student static key is allowed.")
    print("  Manual test: connect with WG, then reconnect with same key without disconnecting.")
    print("  Does the old session get killed? Does the server send any notification?")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from encryption.session import WireguardSession, SERVER_STATIC_PUBLIC_KEY
        import os as _os
        priv_hex = _os.environ.get('WG_STATIC_PRIVATE')
        pub_hex  = _os.environ.get('WG_STATIC_PUBLIC')
        if priv_hex and pub_hex:
            import asyncio

            async def test_wg_double_connect():
                priv = bytes.fromhex(priv_hex)
                pub  = bytes.fromhex(pub_hex)
                s1 = WireguardSession(priv, pub)
                await s1.connect('csc4026z.link', 51820)
                print(f"  WG Session 1: session={s1.chat_session}, user={s1.username}")

                s2 = WireguardSession(priv, pub)
                await s2.connect('csc4026z.link', 51820)
                print(f"  WG Session 2: session={s2.chat_session}, user={s2.username}")

                import msgpack
                ping1 = msgpack.packb({'request_type': 3, 'session': s1.chat_session, 'request_handle': make_handle()})
                await s1.send(ping1)
                try:
                    r = await asyncio.wait_for(s1.receive(), timeout=3.0)
                    print(f"  WG Session 1 still alive after S2 connected: {msgpack.unpackb(r, raw=True)}")
                except asyncio.TimeoutError:
                    print(f"  WG Session 1 KILLED after S2 connected — single-session enforced")

                await s2.close()

            asyncio.run(test_wg_double_connect())
        else:
            print("  (Skipped — WG_STATIC_PRIVATE/PUBLIC not set)")
    except Exception as e:
        print(f"  WG double-connect test error: {e}")

    report(
        'PROBE 24 — Reconnect / Session Uniqueness',
        "Multiple sessions allowed from same client, or WG single-session not enforced",
        {'both_cleartext_active': both_active},
        False,  # Cleartext allows multiple sessions by design
        evidence="Cleartext allows multiple sessions (expected). WG single-session enforcement tested separately."
    )

if __name__ == '__main__':
    run()
