"""
PROBE 07 — Channel Message Without Joining
Hypothesis: Can you send a message to a channel you haven't joined?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, recv_all, report

def run():
    sock_a, session_a, username_a = connect_cleartext()
    sock_b, session_b, username_b = connect_cleartext()

    channel_name = f"probe-{random.randint(1000, 9999)}"

    # User A creates (and auto-joins) the channel
    r_create = send_recv(sock_a, {
        'request_type': 4, 'session': session_a,
        'request_handle': make_handle(),
        'channel': channel_name, 'description': 'probe channel'
    })
    print(f"A creates channel {channel_name}: {r_create}")

    # User B does NOT join — tries to send a message directly
    r_msg = send_recv(sock_b, {
        'request_type': 9, 'session': session_b,
        'request_handle': make_handle(),
        'channel': channel_name, 'message': 'unauthorized message'
    })
    print(f"B sends message without joining: {r_msg}")
    msg_accepted = r_msg and r_msg.get(b'response_type') not in (None, 20)

    # Does user A receive the message anyway?
    msgs = recv_all(sock_a, 3, timeout=2.0)
    print(f"Messages received by channel member A: {msgs}")
    msg_delivered = any(
        m.get(b'message') == b'unauthorized message' for m in msgs
    )

    # Send to a channel that doesn't exist
    r_ghost = send_recv(sock_b, {
        'request_type': 9, 'session': session_b,
        'request_handle': make_handle(),
        'channel': 'definitely-does-not-exist',
        'message': 'ghost message'
    })
    print(f"B sends message to nonexistent channel: {r_ghost}")

    # Cleanup
    send_recv(sock_a, {
        'request_type': 8, 'session': session_a,
        'request_handle': make_handle(), 'channel': channel_name
    })
    sock_a.close()
    sock_b.close()

    vulnerable = msg_accepted or msg_delivered
    report(
        'PROBE 07 — Channel Message Without Joining',
        "Message to unjoined channel is accepted or delivered to members",
        {'msg_accepted': msg_accepted, 'msg_delivered': msg_delivered},
        vulnerable,
        evidence=f"Accepted={msg_accepted}, Delivered={msg_delivered}"
    )

if __name__ == '__main__':
    run()
