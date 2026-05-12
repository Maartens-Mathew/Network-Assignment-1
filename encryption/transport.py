import struct

from .primitives import AEAD_encrypt, AEAD_decrypt


def wrap_message(plaintext: bytes, send_key: bytes,
                 counter: int, receiver_index: int) -> bytes:
    """
    Encrypt a msgpack chat message into a Wireguard transport packet (Section 5.4.6).

    Args:
        plaintext:      raw msgpack bytes of the chat message
        send_key:       T_I_send derived from handshake
        counter:        N_I_send (increment after each call)
        receiver_index: server's sender index from handshake response

    Returns:
        raw bytes of the complete transport packet
    """
    encrypted = AEAD_encrypt(send_key, counter, plaintext, b'')

    packet = (
        b'\x04'                              # type
        + b'\x00\x00\x00'                   # reserved
        + struct.pack('<I', receiver_index)  # receiver (little-endian u32)
        + struct.pack('<Q', counter)         # counter (little-endian u64)
        + encrypted
    )
    return packet


def unwrap_message(packet: bytes, recv_key: bytes, counter: int) -> bytes:
    """
    Decrypt a Wireguard transport packet into plaintext msgpack bytes (Section 5.4.6).

    Args:
        packet:   raw UDP packet bytes
        recv_key: T_I_recv derived from handshake
        counter:  N_I_recv (increment after each call)

    Returns:
        plaintext msgpack bytes

    Raises:
        ValueError if packet type is wrong or decryption fails
    """
    if packet[0] != 0x04:
        raise ValueError(f"Expected transport packet (0x04), got {hex(packet[0])}")

    # type(1) + reserved(3) + receiver(4) + counter(8) = 16 bytes header
    msg_counter = struct.unpack('<Q', packet[8:16])[0]
    encrypted   = packet[16:]

    plaintext = AEAD_decrypt(recv_key, msg_counter, encrypted, b'')
    return plaintext
