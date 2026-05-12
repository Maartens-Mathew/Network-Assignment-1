"""
PROBE 19 — Channel Name Injection
Hypothesis: Channel names restricted to letters, numbers, underscores, dashes.
Does the server enforce this?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    invalid_names = [
        ('test channel',        'space'),
        ('test.channel',        'dot'),
        ('test@channel',        'at sign'),
        ('test/channel',        'slash'),
        ('../etc/passwd',       'path traversal'),
        ('test\x00channel',     'null byte'),
        ('test\nchannel',       'newline'),
        ('',                    'empty'),
        ('a' * 21,              'over 20 char limit'),
        ('!@#$%^&*()',          'special chars'),
        ('-startdash',          'starts with dash'),
        ('_startunder',         'starts with underscore'),
        ('1startnum',           'starts with number'),
        ('UPPERCASE',           'uppercase'),
        ('MiXeDcAsE',           'mixed case'),
        ('test-channel_ok',     'valid: dash and underscore'),
        ('a' * 20,              'exactly 20 chars (valid)'),
        ('a' * 19,              '19 chars (valid)'),
    ]

    results = {}
    unexpected_accepts = []
    for name, label in invalid_names:
        response = send_recv(sock, {
            'request_type': 4, 'session': session,
            'request_handle': make_handle(),
            'channel': name, 'description': 'injection test'
        })
        success = response and response.get(b'response_type') == 25
        results[label] = 'CREATED' if success else f"ERROR: {response.get(b'error') if response else 'timeout'}"
        print(f"  {label} ({repr(name)[:30]}): {results[label]}")

        if success:
            # Cleanup immediately
            send_recv(sock, {
                'request_type': 8, 'session': session,
                'request_handle': make_handle(), 'channel': name
            })
            # Only flag if it's actually invalid
            if label not in ('valid: dash and underscore', 'exactly 20 chars (valid)', '19 chars (valid)'):
                unexpected_accepts.append(label)
        time.sleep(0.15)

    sock.close()

    vulnerable = len(unexpected_accepts) > 0
    report(
        'PROBE 19 — Channel Name Injection',
        "Invalid channel names (spaces, special chars, over length) accepted",
        results,
        vulnerable,
        evidence=f"Unexpected accepts: {unexpected_accepts}" if unexpected_accepts else "All invalid names rejected"
    )

if __name__ == '__main__':
    run()
