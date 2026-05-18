from dataclasses import dataclass

from features.channels.model.channel import Channel
from features.users.model.transport_type import TransportType


@dataclass
class User:
    username : str

@dataclass
class UserInfo:
    username : User
    channels : list[Channel]
    transport : TransportType
    public_key : str