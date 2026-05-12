import hashlib
import struct
import time

import nacl.bindings
import nacl.public
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

CONSTRUCTION = b"Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s"
IDENTIFIER   = b"WireGuard v1 zx2c4 Jason@zx2c4.com"
LABEL_MAC1   = b"mac1----"
LABEL_COOKIE = b"cookie--"
ZERO_KEY     = b'\x00' * 32


def DH_Generate():
    private_key = nacl.public.PrivateKey.generate()
    return (bytes(private_key), bytes(private_key.public_key))


def DH(private_key, public_key):
    return nacl.bindings.crypto_scalarmult(n=private_key, p=public_key)


def Hash(data):
    # Spec says BLAKE2b but test vectors (and server) match BLAKE2s-32.
    # Python 3.14 corrected BLAKE2b behavior diverges from the pre-3.14
    # implementation that the server was built against.
    return hashlib.blake2s(data, digest_size=32).digest()


def MixHash(a, b):
    return Hash(a + b)


def Mac(key, data):
    return hashlib.blake2s(data, key=key, digest_size=16).digest()


def Hmac(key, data):
    BLOCK_SIZE = 64  # BLAKE2s block size in bytes (spec says 128 for BLAKE2b, but we use BLAKE2s)

    if len(key) > BLOCK_SIZE:
        key = Hash(key)
    key = key + b'\x00' * (BLOCK_SIZE - len(key))

    ipad = bytes(b ^ 0x36 for b in key)
    opad = bytes(b ^ 0x5c for b in key)

    inner = Hash(ipad + data)
    return Hash(opad + inner)


def Kdf1(key, input):
    t0 = Hmac(key, input)
    t1 = Hmac(t0, b'\x01')
    return t1


def Kdf2(key, input):
    t0 = Hmac(key, input)
    t1 = Hmac(t0, b'\x01')
    t2 = Hmac(t0, t1 + b'\x02')
    return t1, t2


def Kdf3(key, input):
    t0 = Hmac(key, input)
    t1 = Hmac(t0, b'\x01')
    t2 = Hmac(t0, t1 + b'\x02')
    t3 = Hmac(t0, t2 + b'\x03')
    return t1, t2, t3


def AEAD_encrypt(key, counter, plaintext, authtext):
    nonce = b'\x00' * 4 + counter.to_bytes(8, 'little')
    return ChaCha20Poly1305(key).encrypt(nonce, plaintext, authtext)


def AEAD_decrypt(key, counter, ciphertext, authtext):
    nonce = b'\x00' * 4 + counter.to_bytes(8, 'little')
    return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, authtext)


def Timestamp():
    t = time.time()
    TAI_OFFSET = 10
    seconds = int(t) + (2 ** 62) + TAI_OFFSET
    nanos = int((t % 1) * 1_000_000_000)
    return struct.pack('>QI', seconds, nanos)


def Timestamp_from(t):
    """Test-only variant that takes a fixed time value instead of using time.time()."""
    TAI_OFFSET = 10
    seconds = int(t) + (2 ** 62) + TAI_OFFSET
    nanos = int((t % 1) * 1_000_000_000)
    return struct.pack('>QI', seconds, nanos)
