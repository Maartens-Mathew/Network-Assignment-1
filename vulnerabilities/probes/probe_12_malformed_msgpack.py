import socket, msgpack, random, time
HOST, PORT = 'csc4026z.link', 51825

def raw_send(payload):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(4.0)
    s.connect((HOST, PORT))
    s.send(payload)
    try:
        r = s.recv(4096)
        try: parsed = msgpack.unpackb(r, raw=True)
        except: parsed = {'raw': r[:80]}
        return parsed
    except socket.timeout:
        return None
    finally:
        s.close()

print('=== PROBE 12: Malformed MessagePack ===\n')

payloads = [
    (b'', 'empty bytes'),
    (b'\x00', 'single null byte'),
    (b'\xff\xff\xff\xff', 'invalid msgpack header'),
    (b'\x81\xa4test', 'truncated map'),
    (b'\x92\x01', 'array missing element'),
    (b'hello world', 'plain text'),
    (b'{"json": true}', 'JSON'),
    (b'\xc1', 'reserved byte 0xc1'),
    (bytes(range(256)), 'all 256 bytes'),
    (b'\x82\xacrequest_type\x01\xaa' + b'\xff' * 100, 'valid start, garbage tail'),
    (b'\x82\xacrequest_type\x03\xaerequest_handle' + b'\x00' * 4, 'truncated handle'),
    (b'\xde\x00\x01' + b'\xa1a\xc0', 'map16 with None value'),
    (b'\xcf' + b'\xff' * 8, 'uint64 max as entire payload'),
    (b'\x81' * 1000, 'repeated map headers'),
    (msgpack.packb({'request_type': 1, 'request_handle': 1}) * 3, 'triple-packed valid msg'),
]

for payload, label in payloads:
    r = raw_send(payload)
    if r is None:
        print(f'  [TIMEOUT ] {label}')
    else:
        rtype = r.get(b'response_type') if isinstance(r, dict) else None
        err = r.get(b'error', b'').decode(errors='replace')[:60] if isinstance(r, dict) else str(r)[:60]
        print(f'  [RESPONSE] {label} → type={rtype} {err}')
    time.sleep(0.3)

print('\nDone.')
