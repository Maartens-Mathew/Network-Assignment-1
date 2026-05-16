from dataclasses import dataclass
from typing import Any

from core.serializable_message import SerializableMessage
from core.types import RequestType


@dataclass
class PingRequest(SerializableMessage):
    session : int
    request_handle : int
    request_type : RequestType = RequestType.PING

    def to_dict(self) -> dict[str, Any]:

        return {
            "request_type": self.request_type,
            "session": self.session,
            "request_handle": self.request_handle,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):

        return cls(
            session = data["session"],
            request_handle = data["request_handle"],
            request_type = data["request_type"],
        )

