from dataclasses import dataclass, field

from core import RequestType
from core.requests.request import Request
from core.responses.channel.channel_join import JoinChannelResponse


@dataclass
class JoinChannelRequest(Request):
    channel : str
    description : str
    request_type : RequestType = field(default = RequestType.CHANNEL_JOIN, init = False)

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "description": self.description,
            "request_type": self.request_type,
            "request_handle": self.request_handle,
            "session": self.session,
        }

    def deserialize(self, data: dict) -> JoinChannelResponse:
        return JoinChannelResponse.from_dict(data)


