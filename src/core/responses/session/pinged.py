from dataclasses import dataclass
from typing import Any

from core.types import ResponseType


@dataclass
class PingResponse(SerializableMessage):
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        pass

    session : int
    response_handle : int
    response_type : ResponseType = ResponseType.PINGED