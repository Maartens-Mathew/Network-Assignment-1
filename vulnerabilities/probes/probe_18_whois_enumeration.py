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

print('=== PROBE 18: WHOIS Enumeration + Info Disclosure ===\n')

sock, sess = connect()

# WHOAMI to get own username
r_self = req(sock, {'request_type': 11, 'session': sess, 'request_handle': h()})
my_name = r_self.get(b'username', b'').decode() if r_self else ''
print(f'Own username: {my_name}\n')

# Full WHOIS on self
r_whois_self = req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(), 'username': my_name})
print(f'WHOIS self — full response:')
if r_whois_self:
    for k, v in r_whois_self.items():
        print(f'  {k}: {v}')
time.sleep(0.2)

# WHOIS nonexistent
r_none = req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(),
                     'username': 'zzz-nonexistent-user-abc123'})
print(f'\nWHOIS nonexistent user:')
if r_none:
    for k, v in r_none.items():
        print(f'  {k}: {v}')
time.sleep(0.2)

# WHOIS empty string
r_empty = req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(), 'username': ''})
print(f'\nWHOIS empty username:')
if r_empty:
    for k, v in r_empty.items():
        print(f'  {k}: {v}')
time.sleep(0.2)

# Enumerate all users via USER_LIST then WHOIS each
r_list = req(sock, {'request_type': 14, 'session': sess, 'request_handle': h(), 'offset': 0})
users = [u.decode() for u in r_list.get(b'users', [])] if r_list else []
print(f'\nAll users online: {users}')

print('\nWHOIS on all online users:')
for user in users:
    w = req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(), 'username': user})
    if not w: continue
    transport = w.get(b'transport', b'').decode()
    pub_key   = w.get(b'wireguard_public_key', b'')
    channels  = [c.decode() for c in w.get(b'channels', [])]
    print(f'  {user}: transport={transport}, pub_key={bool(pub_key)}, channels={channels}')
    if pub_key:
        print(f'    !! PUBLIC KEY: {pub_key.hex()}')
    time.sleep(0.15)

# Timing oracle — does WHOIS take longer for existing vs nonexistent?
import time as t
timing = {}
for username in ['zzz-nonexistent-abc', my_name]:
    times = []
    for _ in range(5):
        start = t.time()
        req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(), 'username': username})
        times.append(t.time() - start)
        time.sleep(0.1)
    timing[username] = sum(times)/len(times)

print(f'\nTiming oracle:')
print(f'  nonexistent user: {timing["zzz-nonexistent-abc"]*1000:.1f}ms avg')
print(f'  existing user:    {timing[my_name]*1000:.1f}ms avg')
diff = abs(timing[my_name] - timing['zzz-nonexistent-abc'])
if diff > 0.05:
    print(f'  !! Timing difference {diff*1000:.1f}ms — potential oracle')
else:
    print(f'  No significant timing difference')

sock.close()
print('\nDone.')
