import socket, msgpack, random, time
HOST, PORT = 'csc4026z.link', 51825

def raw_req(payload):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(4.0)
    s.connect((HOST, PORT))
    s.send(payload)
    try:
        r = msgpack.unpackb(s.recv(4096), raw=True)
        s.close()
        return r
    except socket.timeout:
        s.close()
        return None

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

print('=== PROBE 16: Session Reuse After Disconnect ===\n')

# Connect, get session, explicitly disconnect
sock, sess = connect()
print(f'Got session: {sess}')
req(sock, {'request_type': 2, 'session': sess, 'request_handle': h()})
sock.close()
print('Disconnected.')
time.sleep(0.5)

# New socket — use old session immediately after disconnect
r1 = raw_req(msgpack.packb({'request_type': 3, 'session': sess, 'request_handle': h()}))
rtype = r1.get(b'response_type') if r1 else None
print(f'PING with old session immediately after disconnect: type={rtype}')
if rtype == 24:
    print('!! VULNERABLE: old session still valid after explicit DISCONNECT')
else:
    print('   Session invalidated on disconnect (safe)')
time.sleep(0.3)

# Try WHOAMI with old session
r2 = raw_req(msgpack.packb({'request_type': 11, 'session': sess, 'request_handle': h()}))
print(f'WHOAMI with old session: type={r2.get(b"response_type") if r2 else None}')
time.sleep(0.3)

# Try to set username with old session
r3 = raw_req(msgpack.packb({'request_type': 13, 'session': sess, 'request_handle': h(),
                              'username': 'clear-reuse'}))
print(f'SET_USERNAME with old session: type={r3.get(b"response_type") if r3 else None}')
time.sleep(0.3)

# Try CREATE CHANNEL with old session
r4 = raw_req(msgpack.packb({'request_type': 4, 'session': sess, 'request_handle': h(),
                              'channel': f'reuse-{random.randint(100,999)}', 'description': 'test'}))
print(f'CHANNEL_CREATE with old session: type={r4.get(b"response_type") if r4 else None}')
time.sleep(0.3)

# Now connect fresh — does same session ID appear?
sock2, sess2 = connect()
print(f'\nNew session after disconnect: {sess2}')
print(f'Same as old? {sess2 == sess}')
sock2.close()

print('\nDone.')
