from fastapi import FastAPI
import socket as soc
import random
import msgpack

def test_endpoint():
    """
    This is the sample code from the lecture. It doesn't
    'do' anything, besides just connect to the server and send a message.

    Just enough to get a working version of the connection; can always build from there.
    """
    message = { 'session': 1, 'request_type': 3,
                'request_handle': random.randint(0, 2**32 - 1)}
    socket = soc.socket(soc.AF_INET, soc.SOCK_DGRAM)
    socket.connect(('csc4026z.link', 51825))
    socket.send(msgpack.packb(message))
    data, addr = socket.recvfrom(4096)
    print(msgpack.unpackb(data))