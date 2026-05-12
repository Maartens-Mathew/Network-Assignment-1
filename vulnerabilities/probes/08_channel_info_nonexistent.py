"""
PROBE 08 — CHANNEL_INFO on Nonexistent / Private Channels
Hypothesis: CHANNEL_INFO may leak information to non-members, or error
messages distinguish "doesn't exist" from "you're not a member."
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    # Query totally nonexistent channel
    r1 = send_recv(sock, {
        'request_type': 6, 'session': session,
        'request_handle': make_handle(), 'channel': 'nonexistent-channel-xyz-abc-123'
    })
    print(f"Nonexistent channel INFO: {r1}")

    # Create a channel with user A, then query with user B (non-member)
    sock_a, session_a, _ = connect_cleartext()
    channel = f"private-{random.randint(1000, 9999)}"
    send_recv(sock_a, {
        'request_type': 4, 'session': session_a,
        'request_handle': make_handle(),
        'channel': channel, 'description': 'secret stuff'
    })
    time.sleep(0.3)

    # User B (sock) queries channel they haven't joined
    r2 = send_recv(sock, {
        'request_type': 6, 'session': session,
        'request_handle': make_handle(), 'channel': channel
    })
    print(f"Non-member CHANNEL_INFO for existing channel: {r2}")

    # Check what's leaked
    members_leaked  = r2 and r2.get(b'members') is not None
    desc_leaked     = r2 and r2.get(b'description') is not None
    info_returned   = r2 and r2.get(b'response_type') not in (None, 20)

    # Check if error messages differ
    err_nonexist = r1.get(b'error') if r1 else None
    err_nonmember = r2.get(b'error') if r2 else None
    errors_differ = err_nonexist != err_nonmember and err_nonexist and err_nonmember
    if errors_differ:
        print(f"Error messages DIFFER:")
        print(f"  nonexistent: {err_nonexist}")
        print(f"  non-member:  {err_nonmember}")

    # Cleanup
    send_recv(sock_a, {
        'request_type': 8, 'session': session_a,
        'request_handle': make_handle(), 'channel': channel
    })
    sock_a.close()
    sock.close()

    vulnerable = members_leaked or desc_leaked or errors_differ
    report(
        'PROBE 08 — CHANNEL_INFO Non-member / Nonexistent',
        "Member lists or descriptions leaked to non-members, or errors reveal channel existence",
        {'members_leaked': members_leaked, 'desc_leaked': desc_leaked, 'errors_differ': errors_differ},
        vulnerable,
        evidence=f"members_leaked={members_leaked}, desc_leaked={desc_leaked}, errors_differ={errors_differ}"
    )

if __name__ == '__main__':
    run()
