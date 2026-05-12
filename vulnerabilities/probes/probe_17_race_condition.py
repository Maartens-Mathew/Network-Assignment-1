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

def h(): return random.randrange(1, 2**32)

print('=== PROBE 17: Username Race Condition ===\n')

# Pre-connect 10 clients
target = f'clear-race{random.randint(1000,9999)}'
print(f'Target username: {target}')
print('Pre-connecting 10 clients...')

clients = []
for _ in range(10):
    s, sess = connect()
    clients.append((s, sess))
    time.sleep(0.05)

results = []
lock = threading.Lock()

def try_claim(sock, session):
    r = req(sock, {'request_type': 13, 'session': session,
                   'request_handle': h(), 'username': target})
    with lock:
        results.append(r)

# Fire all simultaneously
threads = [threading.Thread(target=try_claim, args=(s, sess)) for s, sess in clients]
print(f'Firing {len(threads)} simultaneous claim attempts...')
for t in threads: t.start()
for t in threads: t.join()

successes = [r for r in results if r and r.get(b'response_type') == 34]
failures  = [r for r in results if r and r.get(b'response_type') != 34]
print(f'\nResults: {len(successes)} succeeded, {len(failures)} failed')
if len(successes) > 1:
    print(f'!! VULNERABLE: {len(successes)} clients simultaneously claimed the same username')
else:
    print('   Server correctly allowed only 1 claim (atomic)')

# Also test: channel creation race — can two clients create the same channel?
channel = f'race-ch-{random.randint(1000,9999)}'
print(f'\nChannel race: {channel}')
ch_results = []

def try_create(sock, session):
    r = req(sock, {'request_type': 4, 'session': session, 'request_handle': h(),
                   'channel': channel, 'description': 'race'})
    with lock:
        ch_results.append(r)

ch_threads = [threading.Thread(target=try_create, args=(s, sess)) for s, sess in clients[:5]]
for t in ch_threads: t.start()
for t in ch_threads: t.join()

ch_ok = [r for r in ch_results if r and r.get(b'response_type') == 25]
print(f'Channel creation: {len(ch_ok)} succeeded simultaneously')
if len(ch_ok) > 1:
    print('!! VULNERABLE: multiple simultaneous channel creations succeeded')

# Cleanup
for s, sess in clients:
    try:
        req(s, {'request_type': 8, 'session': sess, 'request_handle': h(), 'channel': channel})
        s.close()
    except: pass

print('\nDone.')
