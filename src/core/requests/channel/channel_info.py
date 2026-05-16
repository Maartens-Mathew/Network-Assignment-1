from dataclasses import dataclass, field
from typing import Any
from core.requests.request import Request
from core.responses.channel.channel_info import ChannelInfoResponse
from core.types import RequestType

@dataclass
class ChannelInfoRequest(Request):
    channel : str
    request_type: RequestType = field(default=RequestType.CHANNEL_INFO, init=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_type": self.request_type.value,
            "request_handle": self.request_handle,
            "session": self.session,
            "channel": self.channel
        }

    def deserialize(self, data: dict) -> ChannelInfoResponse:
        return ChannelInfoResponse.from_dict(data)