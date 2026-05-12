"""
PROBE 01 — Session Fixation
Hypothesis: Can you include a session field in CONNECT and have the server
accept or use it, allowing you to pick your own session ID?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import socket
import msgpack
from vulnerabilities.lib.probe import (
    SERVER_HOST, CLEAR_PORT, make_handle, connect_cleartext,
    send_recv, send_raw, report
)

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    sock.connect((SERVER_HOST, CLEAR_PORT))

    # Attempt 1: CONNECT with arbitrary session value
    handle = make_handle()
    sock.send(msgpack.packb({
        'request_type': 1,
        'request_handle': handle,
        'session': 12345678
    }))
    r1 = msgpack.unpackb(sock.recv(4096), raw=True)
    print(f"CONNECT with session=12345678: {r1}")
    assigned = r1.get(b'session')
    fixed_accepted = assigned == 12345678
    if not fixed_accepted:
        print(f"  Server assigned session: {assigned} (different — good)")
    sock.close()

    # Attempt 2: CONNECT with session=0
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.settimeout(5.0)
    sock2.connect((SERVER_HOST, CLEAR_PORT))
    r2 = send_raw(sock2, msgpack.packb({'request_type': 1, 'request_handle': make_handle(), 'session': 0}))
    print(f"CONNECT with session=0: {r2}")
    sock2.close()

    # Attempt 3: CONNECT with session=1
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock3.settimeout(5.0)
    sock3.connect((SERVER_HOST, CLEAR_PORT))
    r3 = send_raw(sock3, msgpack.packb({'request_type': 1, 'request_handle': make_handle(), 'session': 1}))
    print(f"CONNECT with session=1: {r3}")
    sock3.close()

    # Attempt 4: CONNECT with session=999999
    sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock4.settimeout(5.0)
    sock4.connect((SERVER_HOST, CLEAR_PORT))
    r4 = send_raw(sock4, msgpack.packb({'request_type': 1, 'request_handle': make_handle(), 'session': 999999}))
    print(f"CONNECT with session=999999: {r4}")
    sock4.close()

    vulnerable = fixed_accepted
    report(
        'PROBE 01 — Session Fixation',
        'Can a client choose its own session ID by including session in CONNECT?',
        r1,
        vulnerable,
        evidence=f"Assigned session was {assigned}, requested 12345678"
    )

if __name__ == '__main__':
    run()
