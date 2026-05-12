import socket
import msgpack
import random
import asyncio
import time
import threading

CONNECT = 1
DISCONNECT = 2
PING = 3

CHANNEL_CREATE = 4
CHANNEL_LIST = 5
CHANNEL_INFO = 6
CHANNEL_JOIN = 7
CHANNEL_LEAVE = 8
CHANNEL_MESSAGE = 9

WHOIS = 10
WHOAMI = 11
USER_MESSAGE = 12
SET_USERNAME = 13
USER_LIST = 14


'''sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(('csc4026z.link', 51825))
sock.send(msgpack.packb({'session': 1, 'request_type':3, 'request_handle': random.randint(0, 2**32 - 1)}))
data, addr = sock.recvfrom(4096)
print(msgpack.unpackb(data))'''


SERVER_HOST = "csc4026z.link"
SERVER_PORT = 51825

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect((SERVER_HOST, SERVER_PORT))

session = None

def background_task():
    while True:
        ping()
        time.sleep(30)

def ping():
    global session
    
    request_handle = random.randrange(0, 2**32)

    ping_request = {
        "session" : session,
        "request_type" : PING,
        "request_handle": request_handle
    }


    packet_data = msgpack.packb(ping_request)
    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)
    response = msgpack.unpackb(data)

    return response

def event_loop():
    '''polls for user input, and sends packets if necessary
    polls for incoming server messages, parsing any that have arrived and updating your local state
    updates your interface'''

def connect():
    #may include the session field
    global session
    request_handle = random.randrange(0, 2**32)

    connect_data = {
        "request_type":CONNECT,
        "request_handle": request_handle
    }

    packet_data = msgpack.packb(connect_data)
    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)
    response = msgpack.unpackb(data, raw=False)

    print("CONNECT response:", response)

    if "session" in response:
        session = response["session"]
        print("Connected. Session:", session)
    else:
        print("Could not connect.")

    return response

def list_channels(offset=None):
    global session
    if session is None:
        print("You are not connected")

    request_handle = random.randrange(0, 2**32)

    channel_request = {
        "request_type" : CHANNEL_LIST,
        "session" : session,
        "request_handle" : request_handle
    }

    if offset is not None:
        channel_request["offset"] = offset


    packet_data = msgpack.packb(channel_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("CHANNEL LIST RESPONSE")
    print(response)

def list_users():

    global session 

    request_handle = random.randrange(0, 2**32)

    list_user_request = {
        "request_type" : USER_LIST,
        "session" : session,
        "request_handle" : request_handle
    }

    packet_data = msgpack.packb(list_user_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw="FALSE")

    print("=============")
    print("LIST_USERS")
    print(response)

def user_info(username):
    global session

    if session is None:
        print("You are not connected")
        return

    request_handle = random.randrange(0, 2**32)

    user_info_request = {
            "request_type": WHOIS,
            "session": session,
            "request_handle": request_handle,
            "username": username
        }

    packet_data = msgpack.packb(user_info_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("=============")
    print("USER_INFO")
    print(response)

    return response


def join_channel(channel):
    global session

    if session is None:
        print("You are not connected")
        return

    request_handle = random.randrange(0, 2**32)

    join_request = {
        "request_type": CHANNEL_JOIN,
        "session": session,
        "request_handle": request_handle,
        "channel": channel
    }

    packet_data = msgpack.packb(join_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("=============")
    print("JOIN_CHANNEL")
    print(response)

    return response

def leave_channel(channel):
    global session

    if session is None:
        print("You are not connected")
        return

    request_handle = random.randrange(0, 2**32)

    leave_request = {
        "request_type": CHANNEL_LEAVE,
        "session": session,
        "request_handle": request_handle,
        "channel": channel
    }

    packet_data = msgpack.packb(leave_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("=============")
    print("LEAVE_CHANNEL")
    print(response)

    return response

def send_messages(channel, message):
    global session

    if session is None:
        print("You are not connected")
        return

    request_handle = random.randrange(0, 2**32)

    message_request = {
        "request_type": CHANNEL_MESSAGE,
        "session": session,
        "request_handle": request_handle,
        "channel": channel,
        "message": message
    }

    packet_data = msgpack.packb(message_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("=============")
    print("SEND MESSAGE")
    print(response)

    return response

def send_DM(username, message):
    global session

    if session is None:
        print("You are not connected")
        return

    request_handle = random.randrange(0, 2**32)

    dm_request = {
        "request_type": USER_MESSAGE,
        "session": session,
        "request_handle": request_handle,
        "username": username,
        "message": message
    }

    packet_data = msgpack.packb(dm_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("=============")
    print("SEND DM")
    print(response)

    return response 

def switch_username(new_username):
    global session

    if session is None:
        print("You are not connected")
        return

    request_handle = random.randrange(0, 2**32)

    username_request = {
        "request_type": SET_USERNAME,
        "session": session,
        "request_handle": request_handle,
        "username": new_username
    }

    packet_data = msgpack.packb(username_request)

    sock.send(packet_data)

    data, addr = sock.recvfrom(4096)

    response = msgpack.unpackb(data, raw=False)

    print("=============")
    print("SWITCH USERNAME")
    print(response)

    return response

def main():

    threading.Thread(target=ping, daemon=True).start()
    connect()
    list_channels()
    list_users()

    

if __name__ == "__main__":
    main()

