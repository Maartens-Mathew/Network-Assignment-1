"""
PROBE 09 — Channel Limit Boundary
Hypothesis: 20-channel-per-user limit — off-by-one allows 21?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()
    created = []

    # Create 20 channels (the maximum)
    for i in range(20):
        channel = f"probe-limit-{i}-{random.randint(100, 999)}"
        response = send_recv(sock, {
            'request_type': 4, 'session': session,
            'request_handle': make_handle(),
            'channel': channel, 'description': f'channel {i}'
        })
        if response and response.get(b'response_type') == 25:
            created.append(channel)
        else:
            print(f"  Channel {i} FAILED: {response}")
        time.sleep(0.1)

    print(f"Successfully created: {len(created)} / 20 channels")

    # Attempt channel 21
    channel_21 = f"probe-overlimit-{random.randint(1000, 9999)}"
    r21 = send_recv(sock, {
        'request_type': 4, 'session': session,
        'request_handle': make_handle(),
        'channel': channel_21, 'description': 'should fail'
    })
    print(f"Channel 21 attempt: {r21}")
    over_limit_accepted = r21 and r21.get(b'response_type') == 25
    if over_limit_accepted:
        created.append(channel_21)

    # Cleanup — leave all created channels
    for channel in created:
        send_recv(sock, {
            'request_type': 8, 'session': session,
            'request_handle': make_handle(), 'channel': channel
        })
        time.sleep(0.1)

    sock.close()

    vulnerable = over_limit_accepted or len(created) > 20
    report(
        'PROBE 09 — Channel Limit Boundary',
        "More than 20 channels created, or off-by-one error at boundary",
        {'created_count': len(created), 'over_limit_accepted': over_limit_accepted},
        vulnerable,
        evidence=f"Created {len(created)} channels, 21st accepted: {over_limit_accepted}"
    )

if __name__ == '__main__':
    run()
