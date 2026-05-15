from enum import IntEnum


class RequestType(IntEnum):
    """
    These enums represent the different types of requests that can be sent to the server.

    Question: Why enums? Why not just hard-code them manually?
    Answer: When you define the shape of the dict variable before you send the message, you can just refer to the
    actual thing you looking for, and not look on the csc2046z website to find what it sai
    """

    #Session flags
    SESSION_CREATE = 1
    SESSION_DESTROY = 2
    PING = 3

    #Channel flags
    CHANNEL_CREATE = 4
    CHANNEL_LIST = 5
    CHANNEL_INFO = 6
    CHANNEL_JOIN = 7
    CHANNEL_LEAVE = 8
    CHANNEL_MESSAGE = 9


    #User flags
    WHOIS = 10
    WHOAMI = 11
    USER_MESSAGE = 12
    SET_USERNAME = 13
    USER_LIST = 14
class ResponseType(IntEnum):

    #Session flags
    SESSION_CREATE = 22
    SESSION_DESTROY = 23
    PING = 24
    OK = 21
    ERROR = 20

    #Server flags
    SERVER_MESSAGE = 36
    SERVER_SHUTDOWN = 37

    #Channel flags
    CHANNEL_CREATE = 25
    CHANNEL_LIST = 26
    CHANNEL_INFO = 27
    CHANNEL_JOIN = 28
    CHANNEL_LEAVE = 29
    CHANNEL_MESSAGE = 30


    #User flags
    WHOIS = 31
    WHOAMI = 32
    USER_MESSAGE = 33
    SET_USERNAME = 34
    USER_LIST = 35