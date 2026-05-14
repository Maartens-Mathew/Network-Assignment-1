# core/requests/request.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from core.types import RequestType
from core.responses.response import Response

R = TypeVar("R", bound=Response)

@dataclass
class Request(ABC, Generic[R]):
    request_type: RequestType
    request_handle: int = field(default=0, init=False)
    session: int = field(default=0, init=False)

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def deserialize(self, data: dict) -> R:
        pass