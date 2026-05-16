from dataclasses import dataclass
from typing import Any

from core.responses.response import Response


@dataclass
class ChannelInfoResponse(Response):
    channel : str
    description : str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChannelInfoResponse :
        if data.get("response_type") == 20:  # ERROR
            raise ValueError(data.get("error", "Unknown server error"))

        return cls(
            session=int(data["session"]),
            response_handle=int(data["response_handle"]),
            channel=str(data["channel"]),
            description=str(data["description"]),
            response_type=data["response_type"]
        )