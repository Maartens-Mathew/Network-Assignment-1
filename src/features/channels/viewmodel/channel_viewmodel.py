import asyncio
from PySide6.QtCore import (
    QObject, 
    Signal, 
    Property, 
    Slot, 
    Qt, 
    QModelIndex,
    QPersistentModelIndex,  
    QAbstractListModel,
    QByteArray
    )
from qasync import asyncSlot

from features.channels.model.channel import Channel, ChannelDetailed
from features.channels.repository.channel_repository import ChannelRepository
from features.channels.viewmodel.channel_state import ChannelState
from utils.error import Error


class ChannelListModel(QAbstractListModel):
    # Ensure your custom roles start past UserRole
    NameRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._channels: list[Channel] = []

    def set_channels(self, channels: list[Channel]):
        self.beginResetModel()
        self._channels = channels
        self.endResetModel()

    def append_channel(self, channel: Channel):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._channels.append(channel)
        self.endInsertRows()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._channels)

    # 2. Insulate your data fetcher from enum-vs-int comparison bugs
    def data(self, index, role : int =Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._channels)):
            return None
        
        channel = self._channels[index.row()]
        
        # Force integer conversion to prevent PySide6 Enum comparison bugs
        if int(role) == int(self.NameRole):
            return channel.name
            
        return None

    # 3. Enforce explicit C++ types for the QML engine
    def roleNames(self):
        return {
            int(self.NameRole): QByteArray(b"name")  # Keys must be ints, values must be QByteArrays
        }


class ChannelsViewModel(QObject):
    channels_changed = Signal()
    selected_channel_changed = Signal()
    state_page_changed = Signal()
    state_changed = Signal(object)
    error_changed = Signal()

    def __init__(self, repository: ChannelRepository):
        super().__init__()
        self.repository = repository

        # Initialize the managed model
        self._channel_model = ChannelListModel(self)
        
        self._selected_channel: Channel | None = None
        self._channel_info: ChannelDetailed | None = None
        self._error: str | None = ""
        self._state_page: int = 1

    def _resolve_channel(self, channel):
        if isinstance(channel, dict):
            return Channel(channel.get("name", ""))
        if isinstance(channel, str):
            return Channel(channel)
        return channel

    # ── QML Accessible Properties ────────────────────────────────────────────

    # Return the QAbstractListModel directly as a QObject
    @Property(QObject, notify=channels_changed)
    def channelModel(self):
        return self._channel_model

    @Property(object, notify=selected_channel_changed)
    def selectedChannel(self):
        if self._selected_channel:
            return {"name": self._selected_channel.name}
        return None

    @property
    def selected_channel(self) -> Channel | None:
        return self._selected_channel

    @Property(int, notify=state_page_changed)
    def statePage(self) -> int:
        return self._state_page

    @Property(str, notify=error_changed)
    def error(self) -> str:
        return self._error or ""

    # ── Async Slots ──────────────────────────────────────────────────────────

    @asyncSlot()
    async def load_channels(self):
        while True:
            self._state_page = 0  # Loading
            self.state_page_changed.emit()
            self.state_changed.emit(ChannelState.LOADING)

            channels = await self.repository.get_channels()
            if isinstance(channels, Error):
                self._error = channels.message
                self.error_changed.emit()
                self._channel_model.set_channels([])
            else:
                # Safely updates the QML view without blowing away delegates
                self._channel_model.set_channels(channels)

            # Adjust UI stack state based on data length managed by the model
            if self._channel_model.rowCount() == 0:
                self._state_page = 1  # Empty
            elif self._selected_channel is None:
                self._state_page = 1
            else:
                self._state_page = 2  # Chat

            self.state_page_changed.emit()
            await asyncio.sleep(3)

    @Slot("QVariant")
    @asyncSlot()
    async def select_channel(self, channel):
        channel = self._resolve_channel(channel)
        if self._selected_channel and self._selected_channel.name == channel.name:
            return
        self._selected_channel = channel
        self.selected_channel_changed.emit()

        self._state_page = 2
        self.state_page_changed.emit()
        self.state_changed.emit(ChannelState.CHANNEL_SELECTED)

    @Slot(QObject)
    @asyncSlot()
    async def join_channel(self, channel: Channel):
        response = await self.repository.join_channel(channel)
        if isinstance(response, Error):
            self._error = response.message
            self.error_changed.emit()
            return

        # Check against list model items
        if not any(c.name == channel.name for c in self._channel_model._channels):
            self._channel_model.append_channel(channel)
            self.state_changed.emit(ChannelState.CHANNEL_JOINED)

    @Slot(str, str)
    @asyncSlot()
    async def create_channel(self, name: str, description: str):
        result = await self.repository.create_channel(
            ChannelDetailed(name=name, description=description)
        )
        if isinstance(result, Error):
            self._error = result.message
            self.error_changed.emit()
        else:
            self._channel_model.append_channel(Channel(name=result.name))
            self.state_changed.emit(ChannelState.CHANNEL_CREATED)