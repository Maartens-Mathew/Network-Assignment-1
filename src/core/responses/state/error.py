from dataclasses import dataclass, field
from typing import Any, Self

from core import ResponseType
from core.responses.response import Response


@dataclass
class ErrorResponse(Response):
    message : str
    response_type : ResponseType = field(init= False, default= ResponseType.ERROR)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            session=data["session"],
            response_handle=data["response_handle"],
            message=data["error"]
        )

