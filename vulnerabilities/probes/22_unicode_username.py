"""
PROBE 22 — Unicode & Encoding Edge Cases in Usernames
Hypothesis: Multi-byte characters, homoglyphs, or invalid UTF-8 sequences
may allow impersonation or bypass the clear- prefix check.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, report

def run():
    sock, session, _ = connect_cleartext()

    unicode_names = [
        ('clear-café',         'café — valid UTF-8 non-ASCII'),
        ('clear-Admin',        'A is \\u0041 — looks like Admin'),
        ('clear-clear',        'c is \\u0063 — Unicode c + lear'),
        ('clear-ｃlear',        'fullwidth c — homoglyph of clear'),
        ('clear-te​st',        'zero-width space in middle'),
        ('clear-‮test',        'right-to-left override'),
        ('clear-̀test',        'combining grave accent'),
        ('ｃlear-test',          'fullwidth c at start — bypasses prefix?'),
        ('cleаr-test',         'Cyrillic a homoglyph of ASCII a'),
    ]

    bypasses = []
    results = {}
    for name, label in unicode_names:
        try:
            response = send_recv(sock, {
                'request_type': 13, 'session': session,
                'request_handle': make_handle(), 'username': name
            })
            success = response and response.get(b'response_type') == 34
            results[label] = 'ACCEPTED' if success else f"REJECTED: {response.get(b'error') if response else 'timeout'}"
            print(f"  {label}: {results[label]}")
            if success and not name.startswith('clear-'):
                bypasses.append(f"{label}: {repr(name)}")
        except Exception as e:
            results[label] = f'Exception: {e}'
            print(f"  {label}: Exception {e}")
        time.sleep(0.2)

    # Also try invalid UTF-8 bytes directly via raw bytes
    try:
        import msgpack
        import socket
        from vulnerabilities.lib.probe import SERVER_HOST, CLEAR_PORT
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        raw_sock.settimeout(5.0)
        raw_sock.connect((SERVER_HOST, CLEAR_PORT))
        # Connect first
        raw_sock.send(msgpack.packb({'request_type': 1, 'request_handle': 12345}))
        raw_data = raw_sock.recv(4096)
        raw_session = msgpack.unpackb(raw_data, raw=True)[b'session']
        # Send SET_USERNAME with raw invalid UTF-8
        raw_sock.send(msgpack.packb({
            'request_type': 13, 'session': raw_session,
            'request_handle': 99999, 'username': b'clear-\xc0\x80test'
        }))
        r = raw_sock.recv(4096)
        print(f"  overlong null UTF-8: {msgpack.unpackb(r, raw=True)}")
        raw_sock.close()
    except Exception as e:
        print(f"  raw UTF-8 test exception: {e}")

    sock.close()

    vulnerable = len(bypasses) > 0
    report(
        'PROBE 22 — Unicode & Encoding Edge Cases',
        "Homoglyphs or invalid encoding allows prefix bypass or impersonation",
        results,
        vulnerable,
        evidence=f"Prefix bypasses: {bypasses}" if bypasses else "No homoglyph or encoding bypasses found"
    )

if __name__ == '__main__':
    run()
