from dataclasses import dataclass

from models import User


@dataclass
class UserMessage:
    sender : User
    message : str

@dataclass
class ChatMessage:
    sender : str
    message : str