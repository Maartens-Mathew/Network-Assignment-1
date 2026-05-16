from dataclasses import dataclass, field
from typing import Any

from core.requests.request import Request
from core.responses.channel.channel_create import CreateChannelResponse
from core.types import RequestType
from features.channels.model.channel import ChannelDetailed


@dataclass
class CreateChannelRequest(Request):
    def deserialize(self, data: dict) -> CreateChannelResponse:
        return CreateChannelResponse.from_dict(data)

    channel_detailed : ChannelDetailed
    request_type : RequestType = field(default = RequestType.CHANNEL_CREATE, init = False)


    def to_dict(self) -> dict[str, Any]:

        return {
            "request_type": int(self.request_type),
            "session": self.session,
            "request_handle": self.request_handle,
            "channel": self.channel_detailed.name,
            "description": self.channel_detailed.description,
        }



