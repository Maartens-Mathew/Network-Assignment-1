"""
PROBE 20 — DM to Nonexistent User
Hypothesis: Error messages may confirm user non-existence. DM to self might
be delivered unexpectedly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from vulnerabilities.lib.probe import make_handle, connect_cleartext, send_recv, recv_all, report

def run():
    sock, session, _ = connect_cleartext()

    # DM to clearly nonexistent user
    r1 = send_recv(sock, {
        'request_type': 12, 'session': session,
        'request_handle': make_handle(),
        'to_username': 'totally-nonexistent-user-xyzabc',
        'message': 'hello?'
    })
    print(f"DM nonexistent user: {r1}")

    # DM to empty username
    r2 = send_recv(sock, {
        'request_type': 12, 'session': session,
        'request_handle': make_handle(),
        'to_username': '',
        'message': 'hello?'
    })
    print(f"DM empty username: {r2}")
    time.sleep(0.2)

    # DM to yourself
    r_whoami = send_recv(sock, {
        'request_type': 11, 'session': session, 'request_handle': make_handle()
    })
    my_username = r_whoami.get(b'username', b'').decode() if r_whoami else ''
    r4 = send_recv(sock, {
        'request_type': 12, 'session': session,
        'request_handle': make_handle(),
        'to_username': my_username,
        'message': 'hi self'
    })
    print(f"DM to self ({my_username}): {r4}")
    time.sleep(0.3)

    # Do you receive your own DM?
    msgs = recv_all(sock, 3, timeout=2.0)
    self_dm_received = any(m.get(b'message') == b'hi self' for m in msgs)
    print(f"Self-DM received: {self_dm_received} ({msgs})")

    # Check if error messages distinguish existence
    err_nonexist = r1.get(b'error') if r1 else None
    err_self     = r4.get(b'error') if r4 else None
    errors_differ = err_nonexist and err_self and err_nonexist != err_self

    sock.close()

    vulnerable = self_dm_received or errors_differ
    report(
        'PROBE 20 — DM to Nonexistent User',
        "DM to self is delivered, or error messages distinguish user existence",
        {'self_dm_received': self_dm_received, 'errors_differ': errors_differ},
        vulnerable,
        evidence=f"self_dm={self_dm_received}, errors_differ={errors_differ} ({err_nonexist!r} vs {err_self!r})"
    )

if __name__ == '__main__':
    run()
