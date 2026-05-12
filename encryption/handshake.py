import os
import struct

from .primitives import (
    Hash, MixHash, DH, DH_Generate, Kdf1, Kdf2, Kdf3,
    AEAD_encrypt, AEAD_decrypt, XAEAD_decrypt, Mac, Timestamp,
    CONSTRUCTION, IDENTIFIER, LABEL_MAC1, LABEL_COOKIE, ZERO_KEY,
)


def build_initiation(static_private: bytes, static_public: bytes,
                     server_public: bytes, cookie: bytes = None) -> tuple:
    """
    Build a Wireguard handshake initiation message (Section 5.4.2).

    Args:
        cookie: if provided (from a prior cookie reply), mac2 is computed as
                Mac(cookie, msg + mac1). Otherwise mac2 is 16 zero bytes.

    Returns:
        (message_bytes, ephemeral_private, chain_key, hash_, sender_index, mac1)
    """
    # 1. Initialise hash and chaining key
    chain_key = Hash(CONSTRUCTION)
    hash_     = MixHash(chain_key, IDENTIFIER)
    hash_     = MixHash(hash_, server_public)

    # 2. Generate ephemeral keypair
    ephemeral_priv, ephemeral_pub = DH_Generate()

    # 3. Mix ephemeral public key into state
    chain_key = Kdf1(chain_key, ephemeral_pub)
    hash_     = MixHash(hash_, ephemeral_pub)

    # 4. Encrypt our static public key
    chain_key, key1 = Kdf2(chain_key, DH(ephemeral_priv, server_public))
    msg_static = AEAD_encrypt(key1, 0, static_public, hash_)
    hash_      = MixHash(hash_, msg_static)

    # 5. Encrypt timestamp
    chain_key, key2 = Kdf2(chain_key, DH(static_private, server_public))
    msg_timestamp   = AEAD_encrypt(key2, 0, Timestamp(), hash_)
    hash_           = MixHash(hash_, msg_timestamp)

    # 6. Assemble packet (without MACs)
    sender_index = int.from_bytes(os.urandom(4), 'little')
    msg = (
        b'\x01'                                    # type
        + b'\x00\x00\x00'                          # reserved
        + struct.pack('<I', sender_index)           # sender (little-endian u32)
        + ephemeral_pub                            # 32 bytes
        + msg_static                               # 48 bytes (32 + 16 tag)
        + msg_timestamp                            # 28 bytes (12 + 16 tag)
    )

    # 7. Calculate mac1: Mac(Hash(Label-Mac1 || S_R_pub), msg)
    mac1_key = Hash(LABEL_MAC1 + server_public)
    mac1     = Mac(mac1_key, msg)

    # mac2 = Mac(cookie, msg + mac1) if we have a cookie, else 16 zero bytes
    mac2 = Mac(cookie, msg + mac1) if cookie is not None else b'\x00' * 16

    full_msg = msg + mac1 + mac2

    return full_msg, ephemeral_priv, chain_key, hash_, sender_index, mac1


def process_response(response_bytes: bytes,
                     ephemeral_priv: bytes,
                     static_priv: bytes,
                     chain_key: bytes,
                     hash_: bytes) -> tuple:
    """
    Parse and validate the server's handshake response (Section 5.4.3).

    Returns:
        (send_key, recv_key, server_index)

    Raises:
        ValueError if the response is invalid or decryption fails
    """
    # type(1) + reserved(3) + sender(4) + receiver(4) + ephemeral(32) + empty_enc(16) + mac1(16) + mac2(16)
    if len(response_bytes) < 92:
        raise ValueError(f"Response too short: {len(response_bytes)} bytes")

    msg_type = response_bytes[0]
    if msg_type != 0x02:
        raise ValueError(f"Expected type 0x02, got {hex(msg_type)}")

    server_index  = struct.unpack('<I', response_bytes[4:8])[0]
    ephemeral_pub = response_bytes[12:44]
    msg_empty_enc = response_bytes[44:60]   # 0-byte plaintext + 16-byte Poly1305 tag

    # Process following Section 5.4.3 from initiator's perspective
    chain_key = Kdf1(chain_key, ephemeral_pub)
    hash_     = MixHash(hash_, ephemeral_pub)
    chain_key = Kdf1(chain_key, DH(ephemeral_priv, ephemeral_pub))
    chain_key = Kdf1(chain_key, DH(static_priv, ephemeral_pub))

    chain_key, tmp, key3 = Kdf3(chain_key, ZERO_KEY)
    hash_     = MixHash(hash_, tmp)

    # Decrypt empty payload — validates the handshake
    plaintext = AEAD_decrypt(key3, 0, msg_empty_enc, hash_)
    if plaintext != b'':
        raise ValueError("Handshake validation failed: empty payload not empty")

    hash_ = MixHash(hash_, msg_empty_enc)

    # Derive transport keys (Section 5.4.5)
    send_key, recv_key = Kdf2(chain_key, b'')

    return send_key, recv_key, server_index


def process_cookie_reply(reply_bytes: bytes, server_public: bytes, mac1: bytes) -> bytes:
    """
    Decrypt the cookie from a WireGuard cookie reply message (Section 5.4.7).

    Cookie reply structure:
        type(1=0x03) + reserved(3) + receiver_index(4) + nonce(24) + encrypted_cookie(32)
        = 64 bytes total
        (cookie is 16 bytes; encrypted form = 16 cookie + 16 Poly1305 tag = 32 bytes)

    Args:
        reply_bytes:   raw UDP packet
        server_public: server's static public key
        mac1:          mac1 from the initiation message that triggered this reply
                       (used as additional data for decryption)

    Returns:
        16-byte cookie to use as mac2 input in the next initiation
    """
    if len(reply_bytes) < 64:
        raise ValueError(f"Cookie reply too short: {len(reply_bytes)} bytes")
    if reply_bytes[0] != 0x03:
        raise ValueError(f"Expected cookie reply (0x03), got {hex(reply_bytes[0])}")

    nonce            = reply_bytes[8:32]   # 24-byte random nonce
    encrypted_cookie = reply_bytes[32:64]  # 16-byte cookie + 16-byte Poly1305 tag

    # Key = Hash(Label-Cookie || S_R_pub)
    cookie_key = Hash(LABEL_COOKIE + server_public)

    return XAEAD_decrypt(cookie_key, nonce, encrypted_cookie, mac1)
