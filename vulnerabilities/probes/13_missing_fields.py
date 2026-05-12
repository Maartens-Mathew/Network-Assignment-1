"""
PROBE 13 — Missing Required Fields
Hypothesis: What happens when required fields are omitted? Server should
return an error, but might crash or leak info.
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
    # CONNECT with no request_handle
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    sock.connect((SERVER_HOST, CLEAR_PORT))
    r1 = send_raw(sock, msgpack.packb({'request_type': 1}))
    print(f"CONNECT no handle: {r1}")
    sock.close()
    time.sleep(0.3)

    # CONNECT with nothing
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    sock.connect((SERVER_HOST, CLEAR_PORT))
    r2 = send_raw(sock, msgpack.packb({}))
    print(f"Empty dict: {r2}")
    sock.close()
    time.sleep(0.3)

    # PING with no session
    sock2, session, _ = connect_cleartext()
    r3 = send_recv(sock2, {'request_type': 3, 'request_handle': make_handle()})
    print(f"PING no session: {r3}")
    time.sleep(0.2)

    # CHANNEL_MESSAGE with no channel field
    r4 = send_recv(sock2, {
        'request_type': 9, 'session': session,
        'request_handle': make_handle(),
        'message': 'no channel specified'
    })
    print(f"CHANNEL_MESSAGE no channel: {r4}")
    time.sleep(0.2)

    # CHANNEL_MESSAGE with no message field
    r5 = send_recv(sock2, {
        'request_type': 9, 'session': session,
        'request_handle': make_handle(),
        'channel': 'some-channel'
    })
    print(f"CHANNEL_MESSAGE no message: {r5}")
    time.sleep(0.2)

    # SET_USERNAME with no username
    r6 = send_recv(sock2, {
        'request_type': 13, 'session': session,
        'request_handle': make_handle()
    })
    print(f"SET_USERNAME no username: {r6}")
    time.sleep(0.2)

    # request_type field missing entirely
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock3.settimeout(5.0)
    sock3.connect((SERVER_HOST, CLEAR_PORT))
    r7 = send_raw(sock3, msgpack.packb({'request_handle': make_handle(), 'session': 1}))
    print(f"No request_type: {r7}")
    sock3.close()

    sock2.close()

    # Check for server crashes (None = timeout)
    crashes = []
    responses = [r1, r2, r3, r4, r5, r6, r7]
    labels    = ['no handle', 'empty', 'no session', 'no channel', 'no message', 'no username', 'no type']
    for label, r in zip(labels, responses):
        if r is None:
            crashes.append(label)

    vulnerable = len(crashes) > 0
    report(
        'PROBE 13 — Missing Required Fields',
        "Server crashes (no response) or leaks internal info on missing fields",
        {'crashes': crashes},
        vulnerable,
        evidence=f"No response (timeout) for: {crashes}" if crashes else "All missing-field cases returned error responses"
    )

if __name__ == '__main__':
    run()
