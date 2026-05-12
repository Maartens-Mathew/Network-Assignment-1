"""
PROBE 10 — Pagination with Invalid / Negative Offsets
Hypothesis: Sending negative, huge, or wrong-typed offset may reveal unexpected data.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    # Normal request
    r0 = send_recv(sock, {
        'request_type': 5, 'session': session,
        'request_handle': make_handle(), 'offset': 0
    })
    print(f"CHANNEL_LIST offset=0: {r0}")

    test_cases = [
        ('offset=65535',   {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': 65535}),
        ('offset=-1',      {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': -1}),
        ('offset=1.5',     {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': 1.5}),
        ('offset=str',     {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': 'ten'}),
        ('USER_LIST -1',   {'request_type': 14, 'session': session, 'request_handle': make_handle(), 'offset': -1}),
        ('USER_LIST big',  {'request_type': 14, 'session': session, 'request_handle': make_handle(), 'offset': 65535}),
        ('offset=None',    {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': None}),
        ('offset=2**32',   {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': 2**32}),
    ]

    issues = []
    for label, msg in test_cases:
        r = send_recv(sock, msg)
        channels = r.get(b'channels', r.get(b'users', [])) if r else []
        normal_channels = r0.get(b'channels', []) if r0 else []
        unexpected = r and r.get(b'response_type') not in (None, 20) and len(channels) > len(normal_channels)
        print(f"  {label}: {r} {'<-- MORE DATA THAN EXPECTED!' if unexpected else ''}")
        if unexpected:
            issues.append(label)
        time.sleep(0.2)

    sock.close()

    vulnerable = len(issues) > 0
    report(
        'PROBE 10 — Negative / Invalid Offset Pagination',
        "Server returns unexpected data or crashes on invalid offset values",
        {'issues': issues},
        vulnerable,
        evidence=f"Issues with: {issues}" if issues else "All invalid offsets handled gracefully"
    )

if __name__ == '__main__':
    run()
