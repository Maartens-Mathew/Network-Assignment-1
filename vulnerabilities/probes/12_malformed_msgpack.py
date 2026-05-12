"""
PROBE 12 — Malformed MessagePack
Hypothesis: Does the server handle all malformed inputs gracefully, or do
some crash / hang it?
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import socket
import msgpack
import time
from vulnerabilities.lib.probe import SERVER_HOST, CLEAR_PORT, report

def run():
    malformed_payloads = [
        (b'',                               'empty'),
        (b'\x00',                           'single null byte'),
        (b'\xff\xff\xff\xff',               'invalid msgpack header'),
        (b'\x81\xa4test',                   'truncated msgpack map'),
        (b'\x92\x01',                       'array with missing element'),
        (b'hello world',                    'plain text'),
        (b'{"json": true}',                 'JSON instead of msgpack'),
        (b'\xc1',                           'reserved msgpack byte 0xc1'),
        (bytes(range(256)),                 'all bytes 0-255'),
        (b'\x82\xacrequest_type\x01' + b'\xaa' * 100,  'valid start, garbage tail'),
    ]

    timeouts = []
    unexpected = []

    for payload, label in malformed_payloads:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        sock.connect((SERVER_HOST, CLEAR_PORT))
        try:
            sock.send(payload)
            data = sock.recv(4096)
            try:
                parsed = msgpack.unpackb(data, raw=True)
                rtype = parsed.get(b'response_type')
                print(f"  {label}: response_type={rtype}")
            except Exception:
                print(f"  {label}: got undecodable response")
                unexpected.append(label)
        except socket.timeout:
            print(f"  {label}: TIMEOUT (no response)")
            timeouts.append(label)
        except Exception as e:
            print(f"  {label}: Exception {e}")
        finally:
            sock.close()
        time.sleep(0.3)

    vulnerable = len(timeouts) > 0
    report(
        'PROBE 12 — Malformed MessagePack',
        "Server hangs (timeout) or crashes on malformed input",
        {'timeouts': timeouts, 'unexpected': unexpected},
        vulnerable,
        evidence=f"Timeouts on: {timeouts}" if timeouts else "All malformed inputs handled — server responded or ignored"
    )

if __name__ == '__main__':
    run()
