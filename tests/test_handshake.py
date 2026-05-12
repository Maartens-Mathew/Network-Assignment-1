import pytest
import struct
from encryption.primitives import (
    Hash, MixHash, Kdf1, Kdf2, Kdf3, AEAD_encrypt, AEAD_decrypt, Mac,
    CONSTRUCTION, IDENTIFIER, LABEL_MAC1, ZERO_KEY, DH
)

# Worked example keys from the assignment spec
EXAMPLE_CLIENT_PRIVATE = b'\x99x\x93eP\xdd\xb7h\xd5dJ\xc7\xa5~\x83\xbdX\x04M\xe29\x15\xe2\xf1\xe8\xd8VFk0\xf8\xa1'
SERVER_PUBLIC          = b'f,^\xc0Cb\xf3\x937\xbf\x11\x14"\xed\x13\x0b\x9f\xe7\xaf;\x94\xb0p\x13\xe1\x94\xdd\x85\xcf\x01\x0bC'

# Fixed ephemeral from worked example
EXAMPLE_EPHEMERAL_PRIV = b'\xac\x03\x18b0\xc4\xf7\xd4*\xa7-\x81&\xfb\xc7\xb3PG0\xae\xa4y0\x90\xe2\xe4\xe2\xa0g\\\x83\xb6'
EXAMPLE_EPHEMERAL_PUB  = b"\xb1\x13\xb4\xd3\x00R'\x8b\x80\xd1\xcc\xc8X\x1bYf(4\xce&\xd0V\xde\x97\xff\xba2$u\x9b\xe3G"


def test_initiation_chain_key_step1():
    """chain_key = Hash(Construction)"""
    result   = Hash(CONSTRUCTION)
    expected = b'`\xe2m\xae\xf3\'\xef\xc0.\xc35\xe2\xa0%\xd2\xd0\x16\xebB\x06\xf8rw\xf5-8\xd1\x98\x8bx\xcd6'
    assert result == expected


def test_initiation_hash_step2():
    """hash = Hash(chain_key || Identifier)"""
    chain_key = Hash(CONSTRUCTION)
    result    = MixHash(chain_key, IDENTIFIER)
    expected  = b'"\x11\xb3a\x08\x1a\xc5fi\x12C\xdbE\x8a\xd52-\x9clf"\x93\xe8\xb7\x0e\xe1\x9ce\xba\x07\x9e\xf3'
    assert result == expected


def test_initiation_hash_step3():
    """hash = Hash(hash || S_R_pub)"""
    chain_key = Hash(CONSTRUCTION)
    hash_     = MixHash(chain_key, IDENTIFIER)
    result    = MixHash(hash_, SERVER_PUBLIC)
    expected  = b'1\xd6\xfb\xdb\xb5F\x13`z\x89\x8cu\xf7,\x8c5x\xa1\xae@#\xf3tu8\xfd\xfe/\xef}\x83\xa1'
    assert result == expected


def test_initiation_chain_key_after_ephemeral():
    """chain_key = Kdf1(chain_key, E_I_pub)"""
    chain_key = Hash(CONSTRUCTION)
    result    = Kdf1(chain_key, EXAMPLE_EPHEMERAL_PUB)
    expected  = b'/U?\xfe\\"\xd6B%\xdb\x94a\xa5\x0b\xf5\x1e\x0f\xbd\r[l\xcd\x08\x07\xc6\xdc\xb4nv\xbfk\t'
    assert result == expected


def test_initiation_msg_static_encryption():
    """Verify msg_static encryption at the correct intermediate state."""
    chain_key = Hash(CONSTRUCTION)
    hash_     = MixHash(chain_key, IDENTIFIER)
    hash_     = MixHash(hash_, SERVER_PUBLIC)
    chain_key = Kdf1(chain_key, EXAMPLE_EPHEMERAL_PUB)
    hash_     = MixHash(hash_, EXAMPLE_EPHEMERAL_PUB)

    dh_result       = DH(EXAMPLE_EPHEMERAL_PRIV, SERVER_PUBLIC)
    chain_key, key1 = Kdf2(chain_key, dh_result)

    import nacl.public
    client_pub = bytes(nacl.public.PrivateKey(EXAMPLE_CLIENT_PRIVATE).public_key)
    msg_static = AEAD_encrypt(key1, 0, client_pub, hash_)
    expected   = b'\xc7\x12ry\x04\xb9\xc3\xaf\x9a\xf4\x7f \xf1\x98\xf3rA\x9d\x92\x0f\xaea[=\xf5N\xe0]Q\x9a\x88\x855\xb046\xb5\xefk\xf4z\xcd#\x0c\x0c\xcd<\xda'
    assert msg_static == expected


def test_mac1_calculation():
    """Verify mac1 matches the worked example."""
    msg = b"\x01\x00\x00\x00Z\r\x85\xee\xb1\x13\xb4\xd3\x00R'\x8b\x80\xd1\xcc\xc8X\x1bYf(4\xce&\xd0V\xde\x97\xff\xba2$u\x9b\xe3G\xc7\x12ry\x04\xb9\xc3\xaf\x9a\xf4\x7f \xf1\x98\xf3rA\x9d\x92\x0f\xaea[=\xf5N\xe0]Q\x9a\x88\x855\xb046\xb5\xefk\xf4z\xcd#\x0c\x0c\xcd<\xda\xc6?XF\x845JvXfm\xf9\xfa0\xf4\xb2\x18\xd6\xf9\x046\x17z\x08\x16y\xa9\xa5"
    mac1_key = Hash(LABEL_MAC1 + SERVER_PUBLIC)
    mac1     = Mac(mac1_key, msg)
    expected = b'/\x1a\x0b\xedH\xbb\xe63\xe8?\xa2bvX\x84\xb3'
    assert mac1 == expected


def test_transport_key_derivation():
    """Verify final transport keys from the worked example."""
    final_chain_key = b"\x12\xa4t\x15\xf3\x1b\xda\xe7\x9b\xe1\xb7\xf7\xc2)\xc1'\xbf\xf6\x03VX\x03b\xfb\x18Y(\nT^\xbe\xa7"
    send_key, recv_key = Kdf2(final_chain_key, b'')
    assert send_key == b'\xd0\x98\xff\xa8\xf4u&\xc4$\x94\xcd&*X\xbfc\x91_\xc3ls\xd1\x1f\xff=\xd4<\x92\xc6\xb5\xb0q'
    assert recv_key == b'\x032\xb2\xbe\xae"<\'}\x97\x08@w\x98\x10l\xb9\xd4|\xc7\x02\xc4\xefE\x18K\x05\x92\xe0d\x8e\xce'


def test_transport_message_encryption():
    """Verify transport message encryption matches worked example."""
    from encryption.transport import wrap_message
    send_key     = b'\xd0\x98\xff\xa8\xf4u&\xc4$\x94\xcd&*X\xbfc\x91_\xc3ls\xd1\x1f\xff=\xd4<\x92\xc6\xb5\xb0q'
    plaintext    = b'\x82\xacrequest_type\x01\xaerequest_handle\xce\xf4\x02\xe7\xd5'
    receiver_idx = 3811305028
    packet       = wrap_message(plaintext, send_key, 0, receiver_idx)
    expected_enc = b"\xb8\xe3ps\xbaB\x17\xdaC9\x0f\xb9\xee\xbb\n\x1d\xe3\x07 \xd1\x88\xb9+\xabS\xc3\\1P#H'\xa84\xe3\x9d\xe9X\x11\xb4uw\xba\x9e\x8a\xefL\x16u\xac\xd0"
    assert packet[16:] == expected_enc


def test_transport_roundtrip():
    """Encrypt then decrypt should return original plaintext."""
    from encryption.transport import wrap_message, unwrap_message
    send_key = recv_key = b'\xd0\x98\xff\xa8\xf4u&\xc4$\x94\xcd&*X\xbfc\x91_\xc3ls\xd1\x1f\xff=\xd4<\x92\xc6\xb5\xb0q'
    plain  = b'\x82\xacrequest_type\x03\xaerequest_handle\xce\x124Vx'
    packet = wrap_message(plain, send_key, 0, 12345)
    result = unwrap_message(packet, recv_key, 0)
    assert result == plain
