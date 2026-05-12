import socket, msgpack, random, time
HOST, PORT = 'csc4026z.link', 51825

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    s.send(msgpack.packb({'request_type': 1, 'request_handle': random.randrange(1, 2**32)}))
    r = msgpack.unpackb(s.recv(4096), raw=True)
    return s, r[b'session']

def req(s, msg):
    s.send(msgpack.packb(msg))
    try: return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout: return None

def h(): return random.randrange(1, 2**32)

print('=== PROBE 06: Cross-Transport DM + WHOIS Info Disclosure ===\n')

sock, sess = connect()

# Get user list
r = req(sock, {'request_type': 14, 'session': sess, 'request_handle': h(), 'offset': 0})
users = [u.decode() for u in r.get(b'users', [])] if r else []
print(f'Users online: {users}\n')

# WHOIS each user — check what's disclosed
wg_users = []
print('--- WHOIS results ---')
for user in users:
    w = req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(), 'username': user})
    if not w: continue
    transport = w.get(b'transport', b'').decode()
    pub_key   = w.get(b'wireguard_public_key', b'')
    channels  = w.get(b'channels', [])
    print(f'  {user}:')
    print(f'    transport: {transport}')
    print(f'    wireguard_public_key: {pub_key.hex() if pub_key else "(none)"}')
    print(f'    channels: {[c.decode() for c in channels]}')
    if transport in ('wireguard', 'wireguard_extended'):
        wg_users.append(user)
        if pub_key:
            print(f'    !! WG public key exposed to cleartext user')
    time.sleep(0.15)

# Try DM to WireGuard users
print(f'\n--- DM attempts to WG users ({len(wg_users)} found) ---')
for user in wg_users[:3]:
    r = req(sock, {'request_type': 12, 'session': sess, 'request_handle': h(),
                   'to_username': user, 'message': 'cross-transport DM probe'})
    rtype = r.get(b'response_type') if r else None
    err   = r.get(b'error', b'').decode(errors='replace') if r else ''
    marker = '!!' if rtype not in (None, 20) else '  '
    print(f'  [{marker}] DM to {user}: type={rtype} {err[:60]}')
    time.sleep(0.2)

# Error message oracle — does rejection reveal user existence?
print('\n--- Error oracle: DM to nonexistent vs WG user ---')
r_nonexist = req(sock, {'request_type': 12, 'session': sess, 'request_handle': h(),
                         'to_username': 'zzz-nonexistent-user-abc', 'message': 'test'})
r_wg = req(sock, {'request_type': 12, 'session': sess, 'request_handle': h(),
                   'to_username': wg_users[0] if wg_users else 'nouser', 'message': 'test'})
print(f'  Error for nonexistent user: {r_nonexist.get(b"error", b"").decode() if r_nonexist else None}')
print(f'  Error for WG user:          {r_wg.get(b"error", b"").decode() if r_wg else None}')
if r_nonexist and r_wg:
    if r_nonexist.get(b'error') != r_wg.get(b'error'):
        print('  !! Different errors — oracle leaks user existence')
    else:
        print('  Same error — no oracle')

sock.close()
print('\nDone.')
