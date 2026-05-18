from dataclasses import dataclass
from typing import Any

from core.responses.response import Response
from features.users.model.user import User


@dataclass
class ConnectResponse(Response):
    session : int
    response_handle : int
    message : str
    username : User

    def to_dict(self) -> dict[str, Any]:
        return {
            "session" : self.session,
            "response_handle" : self.response_handle,
            "message" : self.message,
            "username" : self.username
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectResponse:
        return cls(
            session = int(data["session"]),
            response_handle = int(data["response_handle"]),
            message = str(data["message"]),
            username = User(str(data["username"])),
            response_type=data["response_type"]
        )