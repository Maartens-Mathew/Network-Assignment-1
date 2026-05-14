from dataclasses import dataclass, field
from typing import Any

from core.requests.request import Request, R
from core.responses.connect import ConnectResponse
from core.types import RequestType


@dataclass
class ConnectRequest(Request):
    def deserialize(self, data: dict) -> ConnectResponse:
        return ConnectResponse.from_dict(data)

    request_type: RequestType = field(default=RequestType.SESSION_CREATE, init=False)



    def to_dict(self) -> dict[str, Any]:

        return {
            "request_handle": self.request_handle,
            "request_type": self.request_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectRequest:

        clazz = cls()
        clazz.request_handle = data["request_handle"]

        return clazz

