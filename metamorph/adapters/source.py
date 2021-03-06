from typing import Any, Dict, List

from database.tables import Event
from metamorph.adapters.base import BaseRepository, PrimaryKey
from metamorph.domain.model import BaseEvent


class EventSourceRepository(BaseRepository):
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

    def delete(self, primary_key: PrimaryKey) -> List[Dict[str, Any]]:
        timestamp = primary_key.get("timestamp")
        event_id = primary_key.get("event_id")
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

    def update(self, primary_key: PrimaryKey) -> List[Dict[str, Any]]:
        timestamp = primary_key.get("timestamp")
        event_id = primary_key.get("event_id")
        sql_command = Event.update({Event.is_processed: True}).where(
            Event.created_at == timestamp and Event.event_id == event_id
        )
        result = sql_command.run_sync()
        return result
