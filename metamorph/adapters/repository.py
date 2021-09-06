from abc import ABC, abstractmethod
from typing import Any, Dict, List, NewType

from database.tables import Event
from metamorph.domain.model import BaseEvent, KafkaBroker

PrimaryKey = NewType("PrimaryKey", Dict[str, str])


class BaseRepository(ABC):
    @abstractmethod
    def add(self, base_event: BaseEvent) -> Any:
        """"""

    @abstractmethod
    def delete(self, keys: PrimaryKey):
        """"""

    @abstractmethod
    def get(self, number_of_rows: int):
        """"""

    @abstractmethod
    def update(self, *args, **kwargs):
        """"""


class EventSourceRepository(ABC):
    def add(self, base_event: BaseEvent) -> Any:
        sql_command = Event.insert(
            Event(
                event_id=base_event.event_id,
                name=base_event.name,
                created_at=base_event.created_at,
                topic_target=base_event.topic_target,
                payload=base_event.payload,
                is_processed=base_event.is_processed,
            )
        )
        result = sql_command.run_sync()
        # This API only returns the first column of a composite key. Piccolo needs some maturing.
        return result

    def delete(self, keys: PrimaryKey) -> List[Dict[str, Any]]:
        timestamp = keys.get("timestamp")
        event_id = keys.get("event_id")
        sql_command = Event.delete().where(
            Event.created_at == timestamp and Event.event_id == event_id
        )
        result = sql_command.run_sync()
        return result

    def get(self, number_of_rows: int):
        sql_command = (
            Event.select()
            .where(Event.is_processed is False)
            .order_by(Event.created_at, ascending=False)
            .limit(number=number_of_rows)
        )
        result = sql_command.run_sync()
        return result

    def update(self, timestamp: float, event_id: str) -> List[Dict[str, Any]]:
        sql_command = Event.update({Event.is_processed: True}).where(
            Event.created_at == timestamp and Event.event_id == event_id
        )
        result = sql_command.run_sync()
        return result


class EventTargetRepository:
    def add(self, kafka_broker: KafkaBroker, event: BaseEvent):
        """"""

    def delete(self, *args, **kwargs):
        return NotImplementedError

    def get(self, *args, **kwargs):
        """"""

    def update(self, *args, **kwargs):
        return NotImplementedError
