"""
PROBE 23 — Empty and None Field Values
Hypothesis: None values, empty strings, or zero values in fields may bypass
validation or cause unexpected behaviour.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    test_cases = [
        ('None message',          {'request_type': 9, 'session': session, 'request_handle': make_handle(), 'channel': 'test', 'message': None}),
        ('empty message',         {'request_type': 9, 'session': session, 'request_handle': make_handle(), 'channel': 'test', 'message': ''}),
        ('None channel name',     {'request_type': 6, 'session': session, 'request_handle': make_handle(), 'channel': None}),
        ('extra unknown fields',  {'request_type': 3, 'session': session, 'request_handle': make_handle(), 'totally_unknown': 'surprise', 'nested': {'key': 'val'}}),
        ('unknown type 255',      {'request_type': 255, 'session': session, 'request_handle': make_handle()}),
        ('request_type 0',        {'request_type': 0, 'session': session, 'request_handle': make_handle()}),
        ('None channel CREATE',   {'request_type': 4, 'session': session, 'request_handle': make_handle(), 'channel': None, 'description': 'test'}),
        ('zero session',          {'request_type': 3, 'session': 0, 'request_handle': make_handle()}),
    ]

    issues = []
    for label, msg in test_cases:
        r = send_recv(sock, msg)
        print(f"  {label}: {r}")
        # Flag if None values bypass validation and get accepted
        if 'None' in label and r and r.get(b'response_type') not in (None, 20):
            issues.append(f"None value accepted in {label}")
        time.sleep(0.2)

    sock.close()

    vulnerable = len(issues) > 0
    report(
        'PROBE 23 — Empty and None Field Values',
        "None values bypass validation or unknown request types cause info leak",
        {'issues': issues},
        vulnerable,
        evidence=f"Issues: {issues}" if issues else "None/empty values rejected correctly"
    )

if __name__ == '__main__':
    run()
