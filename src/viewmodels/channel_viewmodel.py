# viewmodels/channel_viewmodel.py
from PySide6.QtCore import QObject, Signal

from models import Error
from models.channel import Channel, ChannelDetailed
from repositories.channel_repository import ChannelRepository
from state.channel_state import ChannelState


class ChannelsViewModel(QObject):
    state_changed = Signal(ChannelState)

    def __init__(self, repository: ChannelRepository):
        super().__init__()
        self.repository = repository

        self.channels: list[Channel] = []
        self.selected_channel: Channel | None = None
        self.channel_info: ChannelDetailed | None = None
        self.error: str | None = None

    async def load_channels(self):
        self.state_changed.emit(ChannelState.LOADING)
        self.channels = await self.repository.get_channels()
        print("Channel information: ")

        for channel in self.channels:
            print(f"Name: {channel.name}")

        self.state_changed.emit(ChannelState.CHANNELS_LOADED)

    async def select_channel(self, channel: Channel):
        self.state_changed.emit(ChannelState.LOADING)
        self.selected_channel = channel
        print(f"Selected channel: {channel.name}")
        self.state_changed.emit(ChannelState.CHANNEL_SELECTED)

    async def join_channel(self, channel: Channel):
        self.state_changed.emit(ChannelState.LOADING)
        response = await self.repository.join_channel(channel)

        if isinstance(response, Error):
            self.error = response.message
            self.state_changed.emit(ChannelState.ERROR)
            return

        # Avoid duplicates if the channel is already in the list.
        if not any(c.name == channel.name for c in self.channels):
            self.channels.append(channel)

        print(f"Joined channel: {channel.name}")
        self.state_changed.emit(ChannelState.CHANNEL_JOINED)

    async def leave_channel(self, channel: Channel):
        self.state_changed.emit(ChannelState.LOADING)
        response = await self.repository.leave_channel(channel)

        if isinstance(response, Error):
            self.error = response.message
            self.state_changed.emit(ChannelState.ERROR)
            return

        print(f"Left channel: {channel.name}")
        self.channels.remove(channel)

        # Clear selection if we just left the selected channel.
        if self.selected_channel and self.selected_channel.name == channel.name:
            self.selected_channel = None

        self.state_changed.emit(ChannelState.CHANNEL_LEFT)

    async def get_channel_info(self, channel: Channel):
        self.state_changed.emit(ChannelState.LOADING)
        result = await self.repository.get_channel_details(channel)

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(ChannelState.ERROR)
            return

        self.channel_info = result
        self.state_changed.emit(ChannelState.CHANNEL_INFO_LOADED)

    async def create_channel(self, name: str, description: str):
        self.state_changed.emit(ChannelState.LOADING)

        result = await self.repository.create_channel(
            ChannelDetailed(name=name, description=description)
        )

        if isinstance(result, Error):
            self.error = result.message
            self.state_changed.emit(ChannelState.ERROR)
        else:
            self.channels.append(Channel(name=result.name))
            self.state_changed.emit(ChannelState.CHANNEL_CREATED)