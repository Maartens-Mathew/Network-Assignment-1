# core/responses/response.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Self
from core import ResponseType



@dataclass
class Response(ABC):
    response_type: ResponseType
    session: int
    response_handle: int

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        pass