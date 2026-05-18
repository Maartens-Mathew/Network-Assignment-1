import datetime
from dataclasses import dataclass


from features.channels.model.channel import Channel
from features.users.model.user import User


@dataclass
class UserMessage:
    sender : User
    message : str

@dataclass
class ChatMessage:
    sender : User
    channel : Channel
    message : str
    time_sent : datetime.datetime