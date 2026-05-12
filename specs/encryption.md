# Encryption Layer — High-Level Spec

## What it does

Every message sent to the chat server travels over an encrypted UDP channel. The encryption is a simplified version of the [WireGuard protocol](https://www.wireguard.com/papers/wireguard.pdf), which handles two things:

1. **Handshake** — proves who you are to the server and establishes a pair of symmetric session keys, without ever sending those keys over the network.
2. **Transport** — wraps every chat message in an authenticated-encryption envelope using those session keys.

Once the handshake completes, both sides can encrypt and decrypt each other's messages. Nobody in the middle can read or tamper with them.

---

## How the handshake works

The protocol involves four keypairs across the two sides:

| Keypair | Owner | Lifetime |
|---------|-------|----------|
| Static | Client (you) | Long-lived — your identity on the server |
| Static | Server | Long-lived — baked into the code |
| Ephemeral | Client | Generated fresh every connection |
| Ephemeral | Server | Generated fresh every connection |

The handshake proceeds in two messages:

### 1. Initiation (client → server)

The client builds a message that mixes together several Diffie-Hellman shared secrets and the current timestamp. None of the secrets travel in plaintext — only public keys and ciphertext are sent. A running `chain_key` and `hash` are updated at every step, binding all earlier material into the final keys.

Key steps:
- Hash the protocol constants to initialise `chain_key` and `hash`
- Generate a fresh ephemeral keypair
- Encrypt the client's static public key (using a secret derived from `DH(ephemeral_client, static_server)`)
- Encrypt a timestamp (using a secret derived from `DH(static_client, static_server)`)
- Append `mac1` — a keyed hash over the whole message, so the server can detect forgeries cheaply

### 2. Response (server → client)

The server generates its own ephemeral keypair, mixes it into the same chain, and sends an empty encrypted payload as a proof that it derived the same session state. The client verifies this before trusting any transport packets.

After the response is verified, both sides run `Kdf2(chain_key, "")` to derive two independent 32-byte keys:
- `send_key` — used by the client to encrypt outgoing messages
- `recv_key` — used by the client to decrypt incoming messages

### Why this is secure

No single piece of information is enough to recover the session keys. An attacker would need to compromise both the client's static private key **and** the ephemeral private key (which is discarded after the handshake). This property is called *forward secrecy*.

---

## How transport messages work

After the handshake, every message is wrapped in a WireGuard transport packet:

```
[type=0x04][reserved][receiver_index][counter][AEAD(plaintext)]
```

- **receiver_index** — the server's handle from the handshake response, so it knows which session this belongs to
- **counter** — a monotonically increasing number, used as the AEAD nonce to prevent replay attacks
- **AEAD** — ChaCha20-Poly1305 authenticated encryption; any tampering causes decryption to fail hard

The counter starts at 0 and increments by 1 for every message sent. It is never reset.

---

## Cryptographic primitives used

| Function | Algorithm | Purpose |
|----------|-----------|---------|
| `DH` | Curve25519 | Diffie-Hellman key exchange |
| `Hash` / `MixHash` | BLAKE2s-256 | Chaining hash during handshake |
| `Mac` | BLAKE2s-128 (keyed) | Message authentication code (mac1) |
| `Hmac` | HMAC-BLAKE2s | Key derivation base |
| `Kdf1/2/3` | HMAC-based KDF | Derive one, two, or three keys |
| `AEAD_encrypt/decrypt` | ChaCha20-Poly1305 | Authenticated encryption |
| `Timestamp` | TAI64N | Replay protection in handshake |

> **Note on BLAKE2:** The WireGuard paper specifies BLAKE2s. The server was built against an older Python where `hashlib.blake2b(data, digest_size=32)` produced BLAKE2s-compatible output. On Python 3.14+ these diverge. The implementation uses `hashlib.blake2s` to stay compatible with the server.

---

## Folder structure

```
encryption/
├── __init__.py       # Public API — re-exports WireguardSession and all primitives
├── primitives.py     # Low-level crypto building blocks
├── handshake.py      # Builds and parses WireGuard handshake messages
├── transport.py      # Wraps/unwraps individual encrypted chat messages
└── session.py        # WireguardSession — the only class teammates need to import
```

### `primitives.py`

All raw cryptographic operations. Nothing here does I/O or holds state. Each function is independently testable against known vectors.

- `DH_Generate()` — generates a fresh Curve25519 keypair `(private, public)`
- `DH(priv, pub)` — Curve25519 scalar multiplication (shared secret)
- `Hash(data)` — BLAKE2s-256 hash, returns 32 bytes
- `MixHash(a, b)` — shorthand for `Hash(a + b)`
- `Mac(key, data)` — keyed BLAKE2s, 16-byte output
- `Hmac(key, data)` — HMAC using BLAKE2s internally, 32-byte output
- `Kdf1/2/3(key, input)` — derive 1, 2, or 3 keys via HMAC-based KDF
- `AEAD_encrypt/decrypt(key, counter, data, authtext)` — ChaCha20-Poly1305
- `Timestamp()` — current time in TAI64N format (12 bytes)

### `handshake.py`

Builds the initiation packet and processes the server's response. Stateless — takes inputs, returns outputs. Holds no connection state.

- `build_initiation(static_priv, static_pub, server_pub)` → `(packet, ephemeral_priv, chain_key, hash_, sender_index)`
- `process_response(response_bytes, ephemeral_priv, static_priv, chain_key, hash_)` → `(send_key, recv_key, server_index)`

### `transport.py`

Wraps and unwraps single messages. No state, no I/O.

- `wrap_message(plaintext, send_key, counter, receiver_index)` → raw UDP packet bytes
- `unwrap_message(packet, recv_key, counter)` → plaintext bytes

### `session.py`

The main class. Manages the socket, runs the handshake, tracks counters, queues incoming messages, and sends periodic pings. This is the only file the rest of the chat client needs to import.

- `WireguardSession(static_private_key, static_public_key)` — construct with your keys
- `await session.connect(host, port)` — handshake + CONNECT message
- `await session.send(msgpack_bytes)` — encrypt and send
- `await session.receive()` → `bytes` — next decrypted message from the server
- `await session.close()` — send DISCONNECT, cancel background tasks, close socket
- `session.connected` — bool property
- `session.chat_session` — session handle returned by the server after CONNECT
- `session.username` — username assigned by the server

### `__init__.py`

Re-exports `WireguardSession` and all primitives from `encryption.primitives` so teammates can import from a single location.

---

## Using the encryption in the chat client

### Setup

Your student keys live in `.env` (gitignored). Load them once at startup:

```python
import os, base64

static_private = bytes.fromhex(os.environ['WG_STATIC_PRIVATE'])
static_public  = bytes.fromhex(os.environ['WG_STATIC_PUBLIC'])
```

Or decode from the base64 values provided on the assignment website:

```python
import base64
static_private = base64.b64decode("your-secret-key-base64==")
# Derive the public key:
import nacl.public
static_public = bytes(nacl.public.PrivateKey(static_private).public_key)
```

### Connecting

```python
import msgpack
from encryption import WireguardSession

session = WireguardSession(static_private, static_public)
await session.connect('csc4026z.link', 51820)

print(session.username)       # assigned by server, e.g. "wireguard_user_12345"
print(session.chat_session)   # integer session handle for subsequent requests
```

### Sending a message

All outgoing messages are msgpack-encoded dicts. The counter and encryption are handled automatically by `session.send()`.

```python
payload = msgpack.packb({
    'request_type':   3,          # PING
    'session':        session.chat_session,
    'request_handle': 12345,      # arbitrary u32, echoed back in the response
})
await session.send(payload)
```

### Receiving a message

`session.receive()` blocks until the next decrypted message arrives. Use `msgpack.unpackb(..., raw=True)` so that string keys come back as bytes (matching the server's encoding).

```python
raw = await session.receive()
msg = msgpack.unpackb(raw, raw=True)
print(msg[b'response_type'])
```

### Closing the session

```python
await session.close()   # sends DISCONNECT, cleans up socket and background tasks
```

### Background behaviour

Once connected, `WireguardSession` runs two background asyncio tasks automatically:

- **`_receive_loop`** — continuously reads UDP packets, decrypts them, and puts plaintext onto an internal queue that `session.receive()` drains
- **`_ping_loop`** — sends a PING every 30 seconds to keep the session alive on the server

These are cancelled automatically when `session.close()` is called.
