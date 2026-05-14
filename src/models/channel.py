from dataclasses import dataclass



@dataclass
class Channel:
    name: str

@dataclass
class ChannelDetailed:
    name : str
    description : str

@dataclass
class ChannelInfo:
    channel : ChannelDetailed
    members : list[User]

