"""
PROBE 03 — Username Prefix Bypass
Hypothesis: The clear- prefix requirement may be bypassable via encoding
tricks, whitespace, or case variations.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    test_usernames = [
        'Clear-test',           # capital C
        'CLEAR-test',           # all caps
        'clear_test',           # underscore instead of dash
        ' clear-test',          # leading space
        'clear-',               # prefix only, empty suffix
        'clear--test',          # double dash
        '\x00clear-test',       # null byte prefix
        'clear-' + 'a'*15,     # max length with prefix
        'a'*20,                 # no prefix at all, max length
        'clEar-test',           # mixed case
        'cle\x61r-test',        # hex encoded 'a' in clear
        '',                     # empty username
        ':clear-test',          # leading colon (colon banned)
        'clear-test:',          # trailing colon
        'clear-te:st',          # colon in middle
    ]

    results = {}
    bypasses = []
    for name in test_usernames:
        response = send_recv(sock, {
            'request_type': 13, 'session': session,
            'request_handle': make_handle(), 'username': name
        })
        success = response and response.get(b'response_type') == 34
        results[repr(name)] = 'ACCEPTED' if success else f"REJECTED: {response}"
        if success and not name.startswith('clear-'):
            bypasses.append(repr(name))
        time.sleep(0.1)

    for name, result in results.items():
        print(f"  {name}: {result}")

    vulnerable = len(bypasses) > 0
    report(
        'PROBE 03 — Username Prefix Bypass',
        "clear- prefix bypassed via encoding tricks, case variation, or special chars",
        results,
        vulnerable,
        evidence=f"Bypassing names: {bypasses}" if bypasses else "No bypasses found"
    )
    sock.close()

if __name__ == '__main__':
    run()
