from enum import IntEnum

class ChannelState(IntEnum):
    LOADING         = 0
    CHANNELS_LOADED = 1
    CHANNEL_SELECTED = 2
    MESSAGES_LOADED = 3
    CHANNEL_CREATED = 4
    ERROR           = 5