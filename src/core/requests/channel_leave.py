from dataclasses import dataclass, field
from typing import Any

from core import RequestType
from core.requests.request import Request, R
from core.responses.channel_join import JoinChannelResponse
from core.responses.channel_leave import LeaveChannelResponse
from core.responses.response import Response


@dataclass
class LeaveChannelRequest(Request):
    channel : str
    request_type : RequestType = field(default = RequestType.CHANNEL_LEAVE, init = False)

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "request_type": self.request_type,
            "request_handle": self.request_handle,
            "session": self.session,
        }

    def deserialize(self, data: dict) -> LeaveChannelResponse:
        return LeaveChannelResponse.from_dict(data)


