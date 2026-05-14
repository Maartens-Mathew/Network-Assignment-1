from abc import ABC, abstractmethod
from typing import Any

import msgpack
from nacl.pwhash import PASSWD_MAX


class SerializableMessage(ABC):

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data : dict[str, Any]):
        pass

    def to_msgpack(self) -> bytes:
        return msgpack.packb(self.to_dict(), use_bin_type=True)