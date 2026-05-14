# viewmodels/channel_viewmodel.py
from PySide6.QtCore import QObject, Signal
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
        self.error: str | None = None

    async def load_channels(self):
        self.state_changed.emit(ChannelState.LOADING)
        self.channels = await self.repository.get_channels()
        self.state_changed.emit(ChannelState.CHANNELS_LOADED)

    async def select_channel(self, channel: Channel):
        self.state_changed.emit(ChannelState.LOADING)
        self.selected_channel = channel
        self.state_changed.emit(ChannelState.CHANNEL_SELECTED)

    async def create_channel(self, name: str, description: str):
        self.state_changed.emit(ChannelState.LOADING)

        result = await self.repository.create_channel(
            ChannelDetailed(name=name, description=description)
        )

        if result is None:
            self.error = "Failed to create channel"
            self.state_changed.emit(ChannelState.ERROR)
        else:
            self.channels.append(result)
            self.state_changed.emit(ChannelState.CHANNEL_CREATED)