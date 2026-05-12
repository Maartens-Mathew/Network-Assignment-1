"""
PROBE 21 — Leave Channel You Never Joined
Hypothesis: CHANNEL_LEAVE on unjoined channel — does it broadcast spurious
leave notifications to legitimate members?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, recv_all, report

def run():
    sock_a, session_a, _ = connect_cleartext()
    sock_b, session_b, _ = connect_cleartext()

    channel = f"probe-leave-{random.randint(1000, 9999)}"

    # A creates and joins the channel
    send_recv(sock_a, {
        'request_type': 4, 'session': session_a,
        'request_handle': make_handle(),
        'channel': channel, 'description': 'leave test'
    })
    time.sleep(0.3)

    # B tries to leave a channel they never joined
    r1 = send_recv(sock_b, {
        'request_type': 8, 'session': session_b,
        'request_handle': make_handle(), 'channel': channel
    })
    print(f"B leaves unjoined channel: {r1}")

    # Does A receive a spurious leave notification?
    msgs = recv_all(sock_a, 3, timeout=2.0)
    spurious = [m for m in msgs if m.get(b'notification_type') in (b'leave', b'channel_leave')]
    print(f"Spurious notifications to member A: {msgs}")
    print(f"  Leave notifications: {spurious}")

    # Leave a nonexistent channel
    r2 = send_recv(sock_b, {
        'request_type': 8, 'session': session_b,
        'request_handle': make_handle(), 'channel': 'nonexistent-xyz-abc'
    })
    print(f"B leaves nonexistent channel: {r2}")

    # Cleanup
    send_recv(sock_a, {
        'request_type': 8, 'session': session_a,
        'request_handle': make_handle(), 'channel': channel
    })
    sock_a.close()
    sock_b.close()

    vulnerable = len(spurious) > 0
    report(
        'PROBE 21 — Leave Unjoined Channel',
        "Spurious leave notifications broadcast when non-member attempts CHANNEL_LEAVE",
        {'spurious_notifications': len(spurious)},
        vulnerable,
        evidence=f"Spurious leave events: {spurious}" if spurious else "No spurious notifications observed"
    )

if __name__ == '__main__':
    run()
