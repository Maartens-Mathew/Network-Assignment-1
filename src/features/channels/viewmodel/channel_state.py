from enum import IntEnum, auto


class ChannelState(IntEnum):
    LOADING         = 0
    CHANNELS_LOADED = 1
    CHANNEL_SELECTED = 2
    MESSAGES_LOADED = 3
    CHANNEL_CREATED = 4
    ERROR           = 5
    CHANNEL_LEFT    = 6
    CHANNEL_JOINED = auto()
    CHANNEL_INFO_LOADED = auto()