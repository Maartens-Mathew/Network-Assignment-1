import pytest
from encryption.primitives import (
    DH, DH_Generate, Hash, MixHash, Mac, Hmac,
    Kdf1, Kdf2, Kdf3, AEAD_encrypt, AEAD_decrypt
)

# ── DH_Generate ────────────────────────────────────────────────────────────────

def test_dh_generate_returns_two_32_byte_values():
    priv, pub = DH_Generate()
    assert len(priv) == 32
    assert len(pub) == 32

def test_dh_generate_is_random():
    priv1, pub1 = DH_Generate()
    priv2, pub2 = DH_Generate()
    assert priv1 != priv2
    assert pub1 != pub2

# ── DH ────────────────────────────────────────────────────────────────────────

def test_dh_known_vector():
    private_key = b'\xb0)e\xdbZ\x01\x8f\x0f\xf5\x91\x88<\xab\x15\x14\x95\xb3\x92\xbd&3\xfe\x18<\x8f\xd6P\xeb\xd0k\xdb\x7f'
    public_key  = b'\x14\xde\xd1\x90m?\x0eaBa\xbb\xf8\\\x08\xdd\xfd\x08\xa7?^\x9f\xcb\x16Y\xdf\xa1\\B\x9d\t7k'
    expected    = b'p\x06\xe4\x7f\xce\x87\x88\xe2\xb9\xd1\xb0\xb7\xf3\x0e}\xb1\xc6{g\xae\x17\x8b\x17{\x91}\x05&\x0cl\xbd:'
    assert DH(private_key, public_key) == expected

def test_dh_shared_secret_symmetric():
    """Both sides of a DH exchange must produce the same secret."""
    priv_a, pub_a = DH_Generate()
    priv_b, pub_b = DH_Generate()
    assert DH(priv_a, pub_b) == DH(priv_b, pub_a)

# ── Hash ──────────────────────────────────────────────────────────────────────

def test_hash_known_vector():
    result = Hash(b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s')
    expected = b'`\xe2m\xae\xf3\'\xef\xc0.\xc35\xe2\xa0%\xd2\xd0\x16\xebB\x06\xf8rw\xf5-8\xd1\x98\x8bx\xcd6'
    assert result == expected

def test_hash_returns_32_bytes():
    assert len(Hash(b'anything')) == 32

def test_hash_is_deterministic():
    assert Hash(b'hello') == Hash(b'hello')

def test_hash_different_inputs_differ():
    assert Hash(b'hello') != Hash(b'world')

# ── MixHash ───────────────────────────────────────────────────────────────────

def test_mixhash_known_vector():
    result   = MixHash(b'a'*50, b'b'*50)
    expected = b'#B\x17\x17\xbe=\xfcc\xd6\xb5@81\t\x8dh\x88\x9b\xb3\xa8\xb9\xb2n\n\x02\r:\xcb\xbe\xb0\xa7\xee'
    assert result == expected

def test_mixhash_equals_hash_of_concat():
    a, b = b'hello', b'world'
    assert MixHash(a, b) == Hash(a + b)

# ── Mac ───────────────────────────────────────────────────────────────────────

def test_mac_known_vector():
    key    = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
    input_ = b'I am a message without a MAC, but only for now.'
    expected = b'*\xbd\x8ak4%\xe4\xb0\xe7\x96\xe5z\x14q\xdd!'
    assert Mac(key, input_) == expected

def test_mac_returns_16_bytes():
    key = b'\x00' * 32
    assert len(Mac(key, b'test')) == 16

def test_mac_different_keys_differ():
    key1 = b'\x00' * 32
    key2 = b'\x01' * 32
    assert Mac(key1, b'test') != Mac(key2, b'test')

# ── Hmac ──────────────────────────────────────────────────────────────────────

def test_hmac_known_vector():
    key    = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
    input_ = b'I am a message without an HMAC, but only for now.'
    expected = b'\x1ew,:\x03\xdd\x0b\x1e\x96\n\x00J\x8c\xe1QzQ\xff\xb8\x02\xcb\xa29\xa8{\x00\x07(\xa6\xc0\x07\xde'
    assert Hmac(key, input_) == expected

def test_hmac_returns_32_bytes():
    assert len(Hmac(b'\x00'*32, b'test')) == 32

# ── Kdf ───────────────────────────────────────────────────────────────────────

KDF_KEY   = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
KDF_INPUT = b'Choose your LLM adventure folks.'

def test_kdf1_known_vector():
    expected = b'0fO\x0e\x0f\xb2\xf4\xaa\xcc\x14\x9c\x84\x8a\xb0D\xd3i\xa6\xac\xbf\xae\xdc^\xd0-D"64X\x93W'
    assert Kdf1(KDF_KEY, KDF_INPUT) == expected

def test_kdf2_known_vector():
    t1_exp = b'0fO\x0e\x0f\xb2\xf4\xaa\xcc\x14\x9c\x84\x8a\xb0D\xd3i\xa6\xac\xbf\xae\xdc^\xd0-D"64X\x93W'
    t2_exp = b'\xaa\x9b\x0fh\xf9\x99z\\%\\\x0f\x8c9L\x7f~<\x1f\xa9G\x9d \x1dw\xba\xc3\x96\x9e\xbb\x8f\x12&'
    t1, t2 = Kdf2(KDF_KEY, KDF_INPUT)
    assert t1 == t1_exp
    assert t2 == t2_exp

def test_kdf3_known_vector():
    t1_exp = b'0fO\x0e\x0f\xb2\xf4\xaa\xcc\x14\x9c\x84\x8a\xb0D\xd3i\xa6\xac\xbf\xae\xdc^\xd0-D"64X\x93W'
    t2_exp = b'\xaa\x9b\x0fh\xf9\x99z\\%\\\x0f\x8c9L\x7f~<\x1f\xa9G\x9d \x1dw\xba\xc3\x96\x9e\xbb\x8f\x12&'
    t3_exp = b'\\\xfb\xc9\xf8!\x88\x03\xa1u\xa8!gUk\xfd\x8b4E|\n5\x89\xb1\xb6\xc1\x1a\x8f\xae?\\\xac)'
    t1, t2, t3 = Kdf3(KDF_KEY, KDF_INPUT)
    assert t1 == t1_exp
    assert t2 == t2_exp
    assert t3 == t3_exp

def test_kdf2_first_output_matches_kdf1():
    assert Kdf2(KDF_KEY, KDF_INPUT)[0] == Kdf1(KDF_KEY, KDF_INPUT)

def test_kdf3_first_two_outputs_match_kdf2():
    t1_3, t2_3, _ = Kdf3(KDF_KEY, KDF_INPUT)
    t1_2, t2_2    = Kdf2(KDF_KEY, KDF_INPUT)
    assert t1_3 == t1_2
    assert t2_3 == t2_2

# ── AEAD ──────────────────────────────────────────────────────────────────────

AEAD_KEY      = b':\xb6\x90\xbd\n:\x18Z88"\xd8a\x08\x9f\xa7\x9c\xc7\xcb\x01\x99-\xfd\x9cGX\xdc\x9dO\x0c\xb3@'
AEAD_AUTHTEXT = b'\x8e2\x89\xe2\x14\xfd\x16\x19o\x06\xc9\xb2\xd9\xe8F\xfd\xdaf\xdc\xa4\xf9\xe9\x98\xbc\xd8x\xb9\x90\x1e\n\xac\x98'
AEAD_PLAIN    = b"attack at dawn"
AEAD_CIPHER   = b'\xfbv\x84\xea\xd0S\n\xc1\x16\x9et\xd5\xa4/\xeee\x9a\xa9MR\xe3\xd5p3\x85\r\xce\x15r\xcd'

def test_aead_encrypt_known_vector():
    assert AEAD_encrypt(AEAD_KEY, 0, AEAD_PLAIN, AEAD_AUTHTEXT) == AEAD_CIPHER

def test_aead_decrypt_known_vector():
    assert AEAD_decrypt(AEAD_KEY, 0, AEAD_CIPHER, AEAD_AUTHTEXT) == AEAD_PLAIN

def test_aead_roundtrip():
    key      = b'\x01' * 32
    plain    = b'hello world this is a test message'
    auth     = b'additional data'
    cipher   = AEAD_encrypt(key, 5, plain, auth)
    recovered = AEAD_decrypt(key, 5, cipher, auth)
    assert recovered == plain

def test_aead_empty_plaintext():
    key    = b'\x00' * 32
    cipher = AEAD_encrypt(key, 0, b'', b'')
    assert AEAD_decrypt(key, 0, cipher, b'') == b''

def test_aead_wrong_key_fails():
    cipher    = AEAD_encrypt(AEAD_KEY, 0, AEAD_PLAIN, AEAD_AUTHTEXT)
    wrong_key = b'\xff' * 32
    with pytest.raises(Exception):
        AEAD_decrypt(wrong_key, 0, cipher, AEAD_AUTHTEXT)

def test_aead_wrong_counter_fails():
    cipher = AEAD_encrypt(AEAD_KEY, 0, AEAD_PLAIN, AEAD_AUTHTEXT)
    with pytest.raises(Exception):
        AEAD_decrypt(AEAD_KEY, 1, cipher, AEAD_AUTHTEXT)
