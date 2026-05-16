from dataclasses import dataclass, field
from typing import Any, Self

from core import ResponseType
from core.responses.response import Response


@dataclass
class ListChannelsResponse(Response):
    response_type: ResponseType = field(default=ResponseType.CHANNEL_LIST, init=False)
    channels: list[str] = field(default_factory=list)
    next_page : bool = field(default=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            session=data["session"],
            response_handle=data["response_handle"],
            channels=data["channels"],
            next_page=data["next_page"]
        )