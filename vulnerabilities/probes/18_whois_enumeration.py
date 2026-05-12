"""
PROBE 18 — User Enumeration via WHOIS
Hypothesis: WHOIS may leak sensitive info (channels, transport, public key),
or timing differences may allow enumerating users.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    # Get own username via WHOAMI
    r_whoami = send_recv(sock, {
        'request_type': 11, 'session': session, 'request_handle': make_handle()
    })
    my_username = r_whoami.get(b'username', b'').decode() if r_whoami else ''
    print(f"My username: {my_username}")

    # WHOIS on nonexistent user
    r1 = send_recv(sock, {
        'request_type': 10, 'session': session,
        'request_handle': make_handle(), 'username': 'nonexistent-user-xyzabc123'
    })
    print(f"WHOIS nonexistent: {r1}")

    # WHOIS on empty string
    r2 = send_recv(sock, {
        'request_type': 10, 'session': session,
        'request_handle': make_handle(), 'username': ''
    })
    print(f"WHOIS empty: {r2}")

    # WHOIS on self
    r4 = send_recv(sock, {
        'request_type': 10, 'session': session,
        'request_handle': make_handle(), 'username': my_username
    })
    print(f"\nWHOIS self ({my_username}):")
    print(f"  channels:             {r4.get(b'channels') if r4 else None}")
    print(f"  transport:            {r4.get(b'transport') if r4 else None}")
    print(f"  wireguard_public_key: {r4.get(b'wireguard_public_key') if r4 else None}")

    # Check timing difference
    timing = {}
    for username in ['nonexistent-xyz-123-abc', my_username]:
        start = time.time()
        send_recv(sock, {
            'request_type': 10, 'session': session,
            'request_handle': make_handle(), 'username': username
        })
        timing[username] = round(time.time() - start, 4)
    print(f"\nWHOIS timing: {timing}")
    timing_diff = abs(timing.get('nonexistent-xyz-123-abc', 0) - timing.get(my_username, 0))
    timing_side_channel = timing_diff > 0.1

    # Check what's disclosed
    channels_leaked = r4 and r4.get(b'channels') is not None
    transport_leaked = r4 and r4.get(b'transport') is not None

    sock.close()

    # Timing side channel is informational rather than definitely vulnerable
    vulnerable = timing_side_channel
    report(
        'PROBE 18 — User Enumeration via WHOIS',
        "WHOIS leaks sensitive fields or timing differences enable enumeration",
        {'channels_in_whois': channels_leaked, 'transport_in_whois': transport_leaked, 'timing_diff_s': timing_diff},
        vulnerable,
        evidence=f"Timing diff={timing_diff:.4f}s (>0.1s = suspicious). channels_leaked={channels_leaked}"
    )

if __name__ == '__main__':
    run()
