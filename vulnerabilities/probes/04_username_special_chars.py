"""
PROBE 04 — Username Special Characters & Length
Hypothesis: The server may not properly validate username length or special
characters, allowing injection or unexpected behaviour.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    test_usernames = [
        ('clear-' + 'a'*100,      'way over 20 char limit'),
        ('clear-' + 'a'*19,       'just over limit'),
        ('clear-' + 'a'*14,       'exactly 20 chars'),
        ('clear-\n',               'newline'),
        ('clear-\t',               'tab'),
        ('clear-\r',               'carriage return'),
        ('clear-test\x00end',      'null byte in middle'),
        ('clear-' + '\xff'*5,      'invalid UTF-8'),
        ('clear-<script>',         'HTML injection'),
        ("clear-'; DROP TABLE",    'SQL injection style'),
        ('clear-../../../etc',     'path traversal style'),
        ('clear-' + '🔥'*3,        'emoji'),
        ('clear-‮',           'right-to-left override'),
    ]

    results = {}
    issues = []
    for name, label in test_usernames:
        try:
            response = send_recv(sock, {
                'request_type': 13, 'session': session,
                'request_handle': make_handle(), 'username': name
            })
            success = response and response.get(b'response_type') == 34
            results[label] = 'ACCEPTED' if success else f"REJECTED: {response}"
            if success:
                issues.append(f"{label}: {repr(name)}")
        except Exception as e:
            results[label] = f'Exception: {e}'
        time.sleep(0.2)

    for label, result in results.items():
        print(f"  {label}: {result}")

    vulnerable = len(issues) > 0
    report(
        'PROBE 04 — Username Special Characters & Length',
        "Server accepts oversized, invalid UTF-8, or injection-style usernames",
        results,
        vulnerable,
        evidence=f"Accepted: {issues}" if issues else "All invalid names rejected"
    )
    sock.close()

if __name__ == '__main__':
    run()
