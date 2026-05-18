# repositories/channel_repository.py
from core.requests import ListChannelsRequest
from core.requests.channel.channel_create import CreateChannelRequest
from core.requests.channel.channel_info import ChannelInfoRequest
from core.requests.channel.channel_leave import LeaveChannelRequest
from core.responses.channel.channel_create import CreateChannelResponse
from core.responses.channel.channel_info import ChannelInfoResponse
from core.responses.channel.channel_leave import LeaveChannelResponse
from core.responses.channel.channel_list import ListChannelsResponse
from core.responses.state.error import ErrorResponse
from network_client.chat_protocol import ChatProtocol
from features.channels.model.channel import Channel, ChannelDetailed
from utils.error import Error


class ChannelRepository:

    def __init__(self, client: ChatProtocol):
        self._client = client  # shared socket, session managed internally

    async def get_channels(self) -> list[Channel] | Error:
        response: ListChannelsResponse | ErrorResponse = await self._client.send_request(
            ListChannelsRequest()
        )

        if isinstance(response, ErrorResponse):
            return Error(response.message)

        return [
            Channel(channel)
            for channel in response.channels
        ]

    async def get_channel_details(self, channel: Channel) -> ChannelDetailed | Error:
        response : ChannelInfoResponse | ErrorResponse = await self._client.send_request(
            ChannelInfoRequest(channel=channel.name)
        )

        if isinstance(response, ErrorResponse):
            return Error(response.message)

        return ChannelDetailed(
            name = response.channel,
            description=response.description
        )


    async def create_channel(self, channel: ChannelDetailed) -> ChannelDetailed | Error:

        response: CreateChannelResponse | ErrorResponse = await self._client.send_request(
            CreateChannelRequest(channel_detailed=channel)
        )

        if isinstance(response, ErrorResponse):
            return Error(response.message)

        return ChannelDetailed(
            name = response.channel,
        description= response.description
        )


    async def join_channel(self, channel: Channel) -> bool | Error:
        response : bool | ErrorResponse = await self._client.send_request(
            ChannelInfoRequest(channel=channel.name)
        )

        if isinstance(response, ErrorResponse):
            return Error(response.message)

        return response

    async def leave_channel(self, channel: Channel) -> bool | Error:

        response : LeaveChannelResponse | ErrorResponse = await self._client.send_request(
            LeaveChannelRequest(
                channel = channel.name
            )
        )

        if isinstance(response, ErrorResponse):
            return False

        return response.channel == channel.name