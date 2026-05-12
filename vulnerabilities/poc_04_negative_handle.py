"""
VULN-04: Negative request handles accepted; zero incorrectly rejected
======================================================================
request_handle is defined in the protocol as a u32 (valid range: 0 to 2^32-1).
The server uses a Python falsy check (if not handle) instead of (if handle is None),
which produces two bugs:

  handle = 0   → rejected as "Handle is required"   (0 is a valid u32)
  handle = -1  → accepted, echoed back in response   (-1 is NOT a valid u32)

The server validates the wrong boundary: it rejects zero (valid) and
accepts negatives (invalid).

Run: uv run python vulnerabilities/poc_04_negative_handle.py
"""
import socket, msgpack, random

HOST, PORT = 'csc4026z.link', 51825

def connect():
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


def main():
    sock, session = connect()
    print('Testing request_handle boundary validation:\n')

    test_cases = [
        (0,            'handle = 0          (valid u32 — should work)'),
        (-1,           'handle = -1         (invalid — should be rejected)'),
        (-1000,        'handle = -1000      (invalid — should be rejected)'),
        (2**32 - 1,    'handle = 2^32 - 1   (max valid u32 — should work)'),
        (2**32,        'handle = 2^32       (overflow — should be rejected)'),
        (2**32 + 1,    'handle = 2^32 + 1   (overflow — should be rejected)'),
    ]

    for handle_val, label in test_cases:
        r = req(sock, {'request_type': 3, 'session': session, 'request_handle': handle_val})
        if r is None:
            outcome = 'TIMEOUT'
        elif r.get(b'response_type') == 24:
            echoed = r.get(b'response_handle')
            outcome = f'ACCEPTED  (echoed handle={echoed})'
        else:
            outcome = f'REJECTED  ({r.get(b"error", b"").decode()})'

        bug = ''
        if handle_val == 0 and 'REJECTED' in outcome:
            bug = '  ← BUG: 0 is a valid u32'
        if handle_val < 0 and 'ACCEPTED' in outcome:
            bug = '  ← BUG: negative is not a valid u32'

        print(f'  {label}')
        print(f'    → {outcome}{bug}')

    sock.close()

    print('\n' + '='*60)
    print('Root cause: server uses  (if not handle)  to check for missing')
    print('handle, treating 0 as "not provided". Correct check would be')
    print('(if handle is None)  combined with  (if not 0 <= handle < 2^32).')


if __name__ == '__main__':
    main()
