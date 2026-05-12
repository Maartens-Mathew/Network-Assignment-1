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

def show(label, r):
    if r is None:
        print(f'  [TIMEOUT ] {label}')
        return
    err = r.get(b'error', b'').decode(errors='replace')[:80] if isinstance(r, dict) else ''
    rtype = r.get(b'response_type') if isinstance(r, dict) else None
    print(f'  [{"RESP   " if rtype else "ERROR  "}] {label} → type={rtype} {err}')

print('=== PROBE 13: Missing Required Fields ===\n')

# No handle in CONNECT
show('CONNECT no handle', raw_req(msgpack.packb({'request_type': 1})))
time.sleep(0.3)

# Completely empty dict
show('Empty dict', raw_req(msgpack.packb({})))
time.sleep(0.3)

# No request_type
show('No request_type', raw_req(msgpack.packb({'request_handle': h(), 'session': 1})))
time.sleep(0.3)

sock, sess = connect()

# PING no session
show('PING no session', req(sock, {'request_type': 3, 'request_handle': h()}))
time.sleep(0.2)

# CHANNEL_MSG no channel
show('CHANNEL_MSG no channel', req(sock, {'request_type': 9, 'session': sess,
     'request_handle': h(), 'message': 'no channel'}))
time.sleep(0.2)

# CHANNEL_MSG no message
show('CHANNEL_MSG no message', req(sock, {'request_type': 9, 'session': sess,
     'request_handle': h(), 'channel': 'some-channel'}))
time.sleep(0.2)

# SET_USERNAME no username
show('SET_USERNAME no username', req(sock, {'request_type': 13, 'session': sess, 'request_handle': h()}))
time.sleep(0.2)

# CHANNEL_INFO no channel
show('CHANNEL_INFO no channel', req(sock, {'request_type': 6, 'session': sess, 'request_handle': h()}))
time.sleep(0.2)

# DM no to_username
show('DM no to_username', req(sock, {'request_type': 12, 'session': sess,
     'request_handle': h(), 'message': 'hello'}))
time.sleep(0.2)

# DM no message
show('DM no message', req(sock, {'request_type': 12, 'session': sess,
     'request_handle': h(), 'to_username': 'someuser'}))
time.sleep(0.2)

# CHANNEL_CREATE no description (optional field — should be fine)
show('CHANNEL_CREATE no description', req(sock, {'request_type': 4, 'session': sess,
     'request_handle': h(), 'channel': f'nodesc-{random.randint(100,999)}'}))
time.sleep(0.2)

# CHANNEL_CREATE no channel name
show('CHANNEL_CREATE no channel name', req(sock, {'request_type': 4, 'session': sess,
     'request_handle': h(), 'description': 'no name'}))
time.sleep(0.2)

sock.close()
print('\nDone.')
