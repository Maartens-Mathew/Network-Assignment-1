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

def recv_all(s, count=5, timeout=2.0):
    s.settimeout(timeout)
    msgs = []
    for _ in range(count):
        try: msgs.append(msgpack.unpackb(s.recv(4096), raw=True))
        except socket.timeout: break
    return msgs

def h(): return random.randrange(1, 2**32)

print('=== PROBE 07: Channel Message Without Joining ===\n')

sock_a, sess_a = connect()
sock_b, sess_b = connect()

channel = f'probe-07-{random.randint(1000,9999)}'

# A creates + joins channel
req(sock_a, {'request_type': 4, 'session': sess_a, 'request_handle': h(),
             'channel': channel, 'description': 'auth test'})
time.sleep(0.2)

# B never joins — tries to send a message
r1 = req(sock_b, {'request_type': 9, 'session': sess_b, 'request_handle': h(),
                  'channel': channel, 'message': 'unauthorized message'})
print(f'B (not joined) sends channel message: response_type={r1.get(b"response_type") if r1 else None}')
if r1:
    print(f'  error: {r1.get(b"error", b"").decode(errors="replace")}')

# Did A receive it?
time.sleep(0.3)
msgs = recv_all(sock_a)
delivered = [m for m in msgs if m.get(b'message')]
print(f'A received {len(delivered)} message(s) from non-member:')
for m in delivered:
    print(f'  !! MESSAGE DELIVERED: {m.get(b"message")}')
if not delivered:
    print('  No messages delivered (safe)')

# B tries to read channel messages (CHANNEL_LIST to see if channel appears)
r2 = req(sock_b, {'request_type': 5, 'session': sess_b, 'request_handle': h(), 'offset': 0})
print(f'\nChannel list visible to non-member: {[c.decode() for c in r2.get(b"channels", [])]}')

# B tries CHANNEL_INFO without joining (already known VULN-01, but confirm)
r3 = req(sock_b, {'request_type': 6, 'session': sess_b, 'request_handle': h(), 'channel': channel})
print(f'CHANNEL_INFO without join: response_type={r3.get(b"response_type") if r3 else None}')

# B tries to send DM as if from within channel context
r4 = req(sock_b, {'request_type': 9, 'session': sess_b, 'request_handle': h(),
                  'channel': 'nonexistent-xyz-channel', 'message': 'ghost'})
print(f'\nMessage to nonexistent channel: response_type={r4.get(b"response_type") if r4 else None}, error={r4.get(b"error", b"").decode(errors="replace") if r4 else None}')

# Cleanup
req(sock_a, {'request_type': 8, 'session': sess_a, 'request_handle': h(), 'channel': channel})
sock_a.close(); sock_b.close()
print('\nDone.')
