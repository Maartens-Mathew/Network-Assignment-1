"""
PROBE 16 — Session ID Reuse After Disconnect
Hypothesis: After explicit DISCONNECT, can the old session ID still be used?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import socket
import msgpack
import time
from vulnerabilities.lib.probe import (
    SERVER_HOST, CLEAR_PORT, make_handle, connect_cleartext,
    send_recv, send_raw, report
)

def run():
    # Connect, get session, explicitly disconnect
    sock, session, username = connect_cleartext()
    print(f"Connected as {username}, session={session}")
    send_recv(sock, {'request_type': 2, 'session': session, 'request_handle': make_handle()})
    sock.close()
    time.sleep(0.5)

    # Open new socket, try to use old session immediately after disconnect
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.settimeout(5.0)
    sock2.connect((SERVER_HOST, CLEAR_PORT))

    r1 = send_raw(sock2, msgpack.packb({
        'request_type': 3, 'session': session, 'request_handle': make_handle()
    }))
    print(f"PING with old session after explicit DISCONNECT: {r1}")
    old_session_works = r1 and r1.get(b'response_type') == 24

    # Try to CONNECT with a previously seen session (session fixation)
    r2 = send_raw(sock2, msgpack.packb({
        'request_type': 1, 'request_handle': make_handle(), 'session': session
    }))
    print(f"CONNECT with previously used session ID: {r2}")
    fixation_accepted = r2 and r2.get(b'session') == session

    sock2.close()

    vulnerable = old_session_works or fixation_accepted
    report(
        'PROBE 16 — Session Reuse After Disconnect',
        "Old session remains usable after explicit DISCONNECT",
        {'old_session_works': old_session_works, 'fixation_accepted': fixation_accepted},
        vulnerable,
        evidence=f"old_session_works={old_session_works}, fixation_accepted={fixation_accepted}"
    )

if __name__ == '__main__':
    run()
