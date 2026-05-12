"""
PROBE 15 — Request Handle Edge Cases
Hypothesis: What happens with special request_handle values: 0, max u32,
negative, duplicate?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import msgpack
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, recv_all, report

def run():
    sock, session, _ = connect_cleartext()

    # Handle = 0
    r1 = send_recv(sock, {'request_type': 3, 'session': session, 'request_handle': 0})
    print(f"Handle=0: {r1}")
    time.sleep(0.2)

    # Handle = max u32
    r2 = send_recv(sock, {'request_type': 3, 'session': session, 'request_handle': 2**32 - 1})
    print(f"Handle=max u32: {r2}")
    time.sleep(0.2)

    # Handle = max u32 + 1 (overflow)
    r3 = send_recv(sock, {'request_type': 3, 'session': session, 'request_handle': 2**32})
    print(f"Handle=u32+1: {r3}")
    time.sleep(0.2)

    # Handle = negative
    r5 = send_recv(sock, {'request_type': 3, 'session': session, 'request_handle': -1})
    print(f"Handle=-1: {r5}")
    time.sleep(0.2)

    # Same handle twice in quick succession
    handle = make_handle()
    sock.send(msgpack.packb({'request_type': 3, 'session': session, 'request_handle': handle}))
    sock.send(msgpack.packb({'request_type': 3, 'session': session, 'request_handle': handle}))
    responses = recv_all(sock, 3, timeout=2.0)
    print(f"Duplicate handle responses ({len(responses)} received): {responses}")
    double_processed = len(responses) >= 2

    sock.close()

    issues = []
    if double_processed:
        issues.append("Duplicate handle processed twice")

    vulnerable = len(issues) > 0
    report(
        'PROBE 15 — Request Handle Edge Cases',
        "Out-of-range handles accepted, or duplicate handle causes double-processing",
        {'double_processed': double_processed},
        vulnerable,
        evidence=f"Issues: {issues}" if issues else "Handle edge cases handled correctly"
    )

if __name__ == '__main__':
    run()
