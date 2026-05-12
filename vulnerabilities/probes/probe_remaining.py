"""
Remaining probes: 19, 20, 21, 22, 23, 24 bundled together.
"""
import socket, msgpack, random, time, threading
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

def recv_all(s, count=5, timeout=2.0):
    s.settimeout(timeout)
    msgs = []
    for _ in range(count):
        try: msgs.append(msgpack.unpackb(s.recv(4096), raw=True))
        except socket.timeout: break
    return msgs

def h(): return random.randrange(1, 2**32)

def show(label, r):
    rtype = r.get(b'response_type') if r else None
    err = r.get(b'error', b'').decode(errors='replace')[:70] if r else 'TIMEOUT'
    ok = rtype not in (None, 20)
    print(f'  {"!!" if ok else "  "} {label} → type={rtype} {err}')
    return ok

# -------------------------------------------------------------------
print('=== PROBE 19: Channel Name Injection ===\n')
sock, sess = connect()

names = [
    ('test channel',   'space'),
    ('test.channel',   'dot'),
    ('test@channel',   'at sign'),
    ('test/channel',   'slash'),
    ('../etc/passwd',  'path traversal'),
    ('test\x00chan',   'null byte'),
    ('test\nchan',     'newline'),
    ('',               'empty'),
    ('a'*21,           '21 chars (over limit)'),
    ('a'*20,           '20 chars (limit)'),
    ('!@#$%^&*()',     'special chars'),
    ('-startdash',     'starts with dash'),
    ('_startunder',    'starts with underscore'),
    ('UPPERCASE',      'uppercase'),
    ('MiXeDcAsE',      'mixed case'),
    ('1startnum',      'starts with number'),
]

for name, label in names:
    r = req(sock, {'request_type': 4, 'session': sess, 'request_handle': h(),
                   'channel': name, 'description': 'injection test'})
    ok = show(label + f' ({repr(name[:15])})', r)
    if ok:
        req(sock, {'request_type': 8, 'session': sess, 'request_handle': h(), 'channel': name})
    time.sleep(0.12)

sock.close()

# -------------------------------------------------------------------
print('\n=== PROBE 20: DM to Nonexistent User + Self DM ===\n')
sock, sess = connect()
r_me = req(sock, {'request_type': 11, 'session': sess, 'request_handle': h()})
my_name = r_me.get(b'username', b'').decode() if r_me else ''

show('DM to nonexistent user', req(sock, {'request_type': 12, 'session': sess,
     'request_handle': h(), 'to_username': 'zzz-nonexistent-abc123', 'message': 'hello'}))
time.sleep(0.2)

show('DM empty username', req(sock, {'request_type': 12, 'session': sess,
     'request_handle': h(), 'to_username': '', 'message': 'hello'}))
time.sleep(0.2)

r_self_dm = req(sock, {'request_type': 12, 'session': sess, 'request_handle': h(),
                        'to_username': my_name, 'message': 'hi self'})
show(f'DM to self ({my_name})', r_self_dm)
time.sleep(0.5)
msgs = recv_all(sock)
self_delivered = [m for m in msgs if m.get(b'message')]
if self_delivered:
    print(f'  !! Self-DM delivered: {self_delivered}')
else:
    print(f'  Self-DM not delivered to own queue')
sock.close()

# -------------------------------------------------------------------
print('\n=== PROBE 21: Leave Channel Never Joined ===\n')
sock_a, sess_a = connect()
sock_b, sess_b = connect()

channel = f'probe21-{random.randint(1000,9999)}'
req(sock_a, {'request_type': 4, 'session': sess_a, 'request_handle': h(),
             'channel': channel, 'description': 'leave test'})
time.sleep(0.2)

show('B leaves channel never joined', req(sock_b, {'request_type': 8, 'session': sess_b,
     'request_handle': h(), 'channel': channel}))
time.sleep(0.3)

spurious = [m for m in recv_all(sock_a) if m.get(b'response_type')]
if spurious:
    print(f'  !! Spurious notifications sent to channel member: {spurious}')
else:
    print('  No spurious notifications (safe)')

show('Leave nonexistent channel', req(sock_b, {'request_type': 8, 'session': sess_b,
     'request_handle': h(), 'channel': 'nonexistent-xyz-999'}))

req(sock_a, {'request_type': 8, 'session': sess_a, 'request_handle': h(), 'channel': channel})
sock_a.close(); sock_b.close()

# -------------------------------------------------------------------
print('\n=== PROBE 22: Unicode / Homoglyph Usernames ===\n')
sock, sess = connect()

unicode_names = [
    ('clear-café',       'é in suffix (valid UTF-8 non-ASCII)'),
    ('clear-ｃlear',      'fullwidth c (homoglyph)'),
    ('clear-te​st',      'zero-width space'),
    ('clear-‮test',      'RTL override (VULN-02 confirm)'),
    ('clear-̀test',      'combining grave accent'),
    ('clear-Admin',      'Unicode A (looks like Admin)'),
    ('clеar-test',       'Cyrillic е (looks like e)'),  # homoglyph attack
]

for name, label in unicode_names:
    try:
        r = req(sock, {'request_type': 13, 'session': sess, 'request_handle': h(), 'username': name})
        ok = show(label, r)
        if ok:
            stored = r.get(b'new_username', b'').decode(errors='replace')
            print(f'     stored: {repr(stored)}')
    except Exception as e:
        print(f'  [EXC] {label}: {e}')
    time.sleep(0.15)

sock.close()

# -------------------------------------------------------------------
print('\n=== PROBE 23: None / Empty / Extra Fields ===\n')
sock, sess = connect()

show('CHANNEL_MSG None message', req(sock, {'request_type': 9, 'session': sess,
     'request_handle': h(), 'channel': 'test', 'message': None}))
time.sleep(0.2)

show('CHANNEL_MSG empty message', req(sock, {'request_type': 9, 'session': sess,
     'request_handle': h(), 'channel': 'test', 'message': ''}))
time.sleep(0.2)

show('CHANNEL_INFO None channel', req(sock, {'request_type': 6, 'session': sess,
     'request_handle': h(), 'channel': None}))
time.sleep(0.2)

show('PING with extra unknown fields', req(sock, {'request_type': 3, 'session': sess,
     'request_handle': h(), 'surprise_field': 'boo', 'nested': {'a': 1}}))
time.sleep(0.2)

show('Unknown request_type 255', req(sock, {'request_type': 255, 'session': sess,
     'request_handle': h()}))
time.sleep(0.2)

show('request_type 0', req(sock, {'request_type': 0, 'session': sess, 'request_handle': h()}))
time.sleep(0.2)

show('session as None', req(sock, {'request_type': 3, 'session': None, 'request_handle': h()}))
time.sleep(0.2)

show('session as list', req(sock, {'request_type': 3, 'session': [1, 2], 'request_handle': h()}))
time.sleep(0.2)

show('message as dict', req(sock, {'request_type': 9, 'session': sess,
     'request_handle': h(), 'channel': 'test', 'message': {'key': 'val'}}))
sock.close()

# -------------------------------------------------------------------
print('\n=== PROBE 24: Multiple Cleartext Sessions Same Source ===\n')
sock1, sess1 = connect()
sock2, sess2 = connect()

print(f'Session 1: {sess1}')
print(f'Session 2: {sess2}')
print(f'Both active simultaneously: {sess1 != sess2}')

r1 = req(sock1, {'request_type': 3, 'session': sess1, 'request_handle': h()})
r2 = req(sock2, {'request_type': 3, 'session': sess2, 'request_handle': h()})
print(f'Session 1 PING: type={r1.get(b"response_type") if r1 else None}')
print(f'Session 2 PING: type={r2.get(b"response_type") if r2 else None}')

# Does connecting session 2 kill session 1?
r1b = req(sock1, {'request_type': 3, 'session': sess1, 'request_handle': h()})
print(f'Session 1 still alive after session 2 connected: {r1b and r1b.get(b"response_type") == 24}')

sock1.close(); sock2.close()
print('\nAll probes done.')
