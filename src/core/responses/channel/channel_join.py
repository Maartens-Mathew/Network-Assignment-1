from dataclasses import dataclass
from typing import Any, Self

from core.responses.response import Response
from core.responses.state.error import ErrorResponse


@dataclass
class JoinChannelResponse(Response):
    channel : str
    description : str
    user : str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self | ErrorResponse:

        if data.get("response_type") == 20:
            return ErrorResponse.from_dict(data)

        return cls(
            session=data["session"],
            response_handle=data["response_handle"],
            channel=data["channel"],
            description=data["description"],
            user=data["user"],
            response_type=data["response_type"]
        )

