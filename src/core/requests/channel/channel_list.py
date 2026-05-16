# core/requests/list_channels_request.py
from dataclasses import dataclass, field
from typing import Any
from core.requests.request import Request
from core.responses.channel.channel_list import ListChannelsResponse
from core.types import RequestType


@dataclass
class ListChannelsRequest(Request):



    request_type: RequestType = field(default=RequestType.CHANNEL_LIST, init=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_type": self.request_type.value,
            "request_handle": self.request_handle,
            "session": self.session,
        }

    def deserialize(self, data: dict) -> ListChannelsResponse:
        return ListChannelsResponse.from_dict(data)