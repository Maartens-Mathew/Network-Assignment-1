from dataclasses import dataclass
from typing import Any

from core.serializable_message import SerializableMessage
from core.types import RequestType


@dataclass
class DisconnectRequest(SerializableMessage):
    request_handle : int
    session : int
    request_type : RequestType = RequestType.SESSION_DESTROY

    def to_dict(self) -> dict[str, Any]:

        return {
            "request_handle": self.request_handle,
            "request_type": self.request_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DisconnectRequest:

        return cls(
            request_handle = data["request_handle"],
            request_type = data["request_type"],
            session = data["session"]
        )

