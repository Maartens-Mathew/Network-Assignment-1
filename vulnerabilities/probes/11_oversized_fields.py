"""
PROBE 11 — Oversized Field Values
Hypothesis: Fields like message (s[500]) and description (s[100]) have
documented max lengths. Does the server enforce these?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    channel = f"probe-size-{random.randint(1000, 9999)}"
    send_recv(sock, {
        'request_type': 4, 'session': session,
        'request_handle': make_handle(),
        'channel': channel, 'description': 'test'
    })
    send_recv(sock, {
        'request_type': 7, 'session': session,
        'request_handle': make_handle(), 'channel': channel
    })
    time.sleep(0.2)

    issues = []

    # Oversized message (spec says s[500])
    r1 = send_recv(sock, {
        'request_type': 9, 'session': session,
        'request_handle': make_handle(),
        'channel': channel, 'message': 'A' * 10000
    })
    print(f"10KB message: {r1}")
    if r1 and r1.get(b'response_type') not in (None, 20):
        issues.append('10KB message accepted')
    time.sleep(0.2)

    # Exactly at limit
    r2 = send_recv(sock, {
        'request_type': 9, 'session': session,
        'request_handle': make_handle(),
        'channel': channel, 'message': 'B' * 500
    })
    print(f"500-byte message (at limit): {r2}")
    time.sleep(0.2)

    # One over limit
    r3 = send_recv(sock, {
        'request_type': 9, 'session': session,
        'request_handle': make_handle(),
        'channel': channel, 'message': 'C' * 501
    })
    print(f"501-byte message (over limit): {r3}")
    if r3 and r3.get(b'response_type') not in (None, 20):
        issues.append('501-byte message accepted (over limit)')
    time.sleep(0.2)

    # Oversized channel description
    r4 = send_recv(sock, {
        'request_type': 4, 'session': session,
        'request_handle': make_handle(),
        'channel': f"probe-desc-{random.randint(100, 999)}",
        'description': 'D' * 10000
    })
    print(f"10KB description: {r4}")
    if r4 and r4.get(b'response_type') not in (None, 20):
        issues.append('10KB description accepted')
    time.sleep(0.2)

    # DM oversized
    r5 = send_recv(sock, {
        'request_type': 12, 'session': session,
        'request_handle': make_handle(),
        'to_username': 'someuser',
        'message': 'E' * 10000
    })
    print(f"10KB DM: {r5}")
    if r5 and r5.get(b'response_type') not in (None, 20):
        issues.append('10KB DM message accepted')
    time.sleep(0.2)

    # Cleanup
    send_recv(sock, {
        'request_type': 8, 'session': session,
        'request_handle': make_handle(), 'channel': channel
    })
    sock.close()

    vulnerable = len(issues) > 0
    report(
        'PROBE 11 — Oversized Field Values',
        "Server accepts messages or descriptions exceeding documented size limits",
        {'issues': issues},
        vulnerable,
        evidence=f"Oversized accepted: {issues}" if issues else "All oversized inputs rejected"
    )

if __name__ == '__main__':
    run()
