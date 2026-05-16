from dataclasses import dataclass
from typing import Any, Self

from core.responses.response import Response

@dataclass
class JoinChannelResponse(Response):
    channel : str
    description : str
    user : str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            session=data["session"],
            response_handle=data["response_handle"],
            channel=data["channel"],
            description=data["description"],
            user=data["user"],
            response_type=data["response_type"]
        )

