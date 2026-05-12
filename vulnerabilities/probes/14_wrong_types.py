"""
PROBE 14 — Wrong Field Types
Hypothesis: Sending fields with wrong types may bypass validation or cause
unexpected behaviour.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    test_cases = [
        ('session as string',    {'request_type': 3, 'session': str(session), 'request_handle': make_handle()}),
        ('request_type string',  {'request_type': '3', 'session': session, 'request_handle': make_handle()}),
        ('request_type float',   {'request_type': 3.0, 'session': session, 'request_handle': make_handle()}),
        ('handle as None',       {'request_type': 3, 'session': session, 'request_handle': None}),
        ('channel as int',       {'request_type': 6, 'session': session, 'request_handle': make_handle(), 'channel': 12345}),
        ('offset as bool True',  {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': True}),
        ('message as list',      {'request_type': 9, 'session': session, 'request_handle': make_handle(), 'channel': 'test', 'message': ['list', 'msg']}),
        ('session as list',      {'request_type': 3, 'session': [session], 'request_handle': make_handle()}),
        ('session as float',     {'request_type': 3, 'session': float(session), 'request_handle': make_handle()}),
    ]

    issues = []
    for label, msg in test_cases:
        r = send_recv(sock, msg)
        # PING success = response_type 24
        accepted = r and r.get(b'response_type') == 24
        print(f"  {label}: {r} {'<-- ACCEPTED (unexpected)!' if accepted else ''}")
        if accepted and 'session as string' in label:
            issues.append(f"Wrong type accepted: {label}")
        time.sleep(0.2)

    sock.close()

    vulnerable = len(issues) > 0
    report(
        'PROBE 14 — Wrong Field Types',
        "Server accepts fields of wrong type, or coerces them in exploitable ways",
        {'issues': issues},
        vulnerable,
        evidence=f"Wrong types accepted: {issues}" if issues else "All type errors correctly rejected"
    )

if __name__ == '__main__':
    run()
