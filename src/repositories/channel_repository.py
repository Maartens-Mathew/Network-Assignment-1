# repositories/channel_repository.py
from core.requests import ListChannelsRequest
from core.requests.channel_create import CreateChannelRequest
from core.responses.channel_create import CreateChannelResponse
from core.responses.channel_list import ListChannelsResponse
from infrastructure.chat_protocol import ChatProtocol
from models.channel import Channel, ChannelDetailed


class ChannelRepository:

    def __init__(self, client: ChatProtocol):
        self._client = client  # shared socket, session managed internally

    async def get_channels(self) -> list[Channel] | None:

        response : ListChannelsResponse = await self._client.send_request(ListChannelsRequest())

        if response.response_type == 20:  # ERROR
            return None


        return [
            Channel(channel)
            for channel in response.channels
        ]

    async def get_channel_details(self, channel: Channel) -> ChannelDetailed | None:
        pass

    async def create_channel(self, channel: ChannelDetailed) -> Channel | None:
        try:
            response : CreateChannelResponse = await self._client.send_request(CreateChannelRequest(
                channel_detailed=channel
            ))
            return Channel(response.channel)
        except ValueError as e:
            print(f"Server error: {e}")
            return None


    async def join_channel(self, channel: Channel) -> bool:
        pass

    async def leave_channel(self, channel: Channel) -> bool:
        pass