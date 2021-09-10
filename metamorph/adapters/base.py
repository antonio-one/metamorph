from abc import ABC, abstractmethod
from typing import Any, Dict, NewType

from metamorph.domain.model import BaseEvent

PrimaryKey = NewType("PrimaryKey", Dict[str, str])


class BaseRepository(ABC):
    @abstractmethod
    def add(self, base_event: BaseEvent) -> Any:
        """"""

    @abstractmethod
    def delete(self, keys: PrimaryKey) -> Any:
        """"""

    @abstractmethod
    def get(self, number_of_rows: int) -> Any:
        """"""

    @abstractmethod
    def update(self, primary_key: PrimaryKey) -> Any:
        """"""
