from dataclasses import dataclass
from typing import Any

from core.responses.response import Response
from core.responses.state.error import ErrorResponse


@dataclass
class CreateChannelResponse(Response):
    channel : str
    description : str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CreateChannelResponse | ErrorResponse:
        if data.get("response_type") == 20:  # ERROR
            return ErrorResponse.from_dict(data)

        return cls(
            session=int(data["session"]),
            response_handle=int(data["response_handle"]),
            channel=str(data["channel"]),
            description=str(data["description"]),
            response_type=data["response_type"]
        )