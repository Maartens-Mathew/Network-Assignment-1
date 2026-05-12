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

def check(label, r):
    if r is None:
        print(f'  [TIMEOUT] {label}')
        return
    rtype = r.get(b'response_type')
    err = r.get(b'error', b'').decode(errors='replace')
    ok = rtype not in (None, 20)
    marker = '!!' if ok else '  '
    print(f'  [{marker}{"ACCEPTED" if ok else "REJECTED "}] {label} → type={rtype} {err[:60] if err else ""}')
    return ok

print('=== PROBE 11: Oversized Fields ===\n')
sock, sess = connect()

channel = f'probe-11-{random.randint(1000,9999)}'
req(sock, {'request_type': 4, 'session': sess, 'request_handle': h(),
           'channel': channel, 'description': 'size test'})
req(sock, {'request_type': 7, 'session': sess, 'request_handle': h(), 'channel': channel})
time.sleep(0.2)

print('--- Channel messages (spec: s[500]) ---')
for size, label in [(499, '499 bytes'), (500, '500 bytes (limit)'), (501, '501 bytes (over)'),
                    (1000, '1000 bytes'), (10000, '10KB'), (65000, '65KB')]:
    r = req(sock, {'request_type': 9, 'session': sess, 'request_handle': h(),
                   'channel': channel, 'message': 'A' * size})
    check(label, r)
    time.sleep(0.2)

print('\n--- Channel descriptions (spec: s[100]) ---')
for size, label in [(99, '99 bytes'), (100, '100 bytes (limit)'), (101, '101 bytes (over)'),
                    (1000, '1000 bytes'), (10000, '10KB')]:
    cname = f'pb11d{random.randint(100,999)}'
    r = req(sock, {'request_type': 4, 'session': sess, 'request_handle': h(),
                   'channel': cname, 'description': 'D' * size})
    check(label, r)
    if r and r.get(b'response_type') == 25:
        req(sock, {'request_type': 8, 'session': sess, 'request_handle': h(), 'channel': cname})
    time.sleep(0.2)

print('\n--- Usernames (spec: s[20]) ---')
for size, label in [(13, '13 bytes (clear-+7)'), (14, '14 bytes (limit: clear-+8)'),
                    (15, '15 bytes (over)'), (20, '20 bytes'), (100, '100 bytes')]:
    name = 'clear-' + 'u' * (size - 6)
    r = req(sock, {'request_type': 13, 'session': sess, 'request_handle': h(), 'username': name})
    check(f'{label} ({repr(name[:25])})', r)
    time.sleep(0.15)

print('\n--- DM messages (spec: s[500]) ---')
r = req(sock, {'request_type': 12, 'session': sess, 'request_handle': h(),
               'to_username': 'someuser', 'message': 'E' * 10000})
check('10KB DM message', r)

# Cleanup
req(sock, {'request_type': 8, 'session': sess, 'request_handle': h(), 'channel': channel})
sock.close()
print('\nDone.')
