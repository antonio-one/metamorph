from datetime import datetime

import pytest
from faker import Faker

from database.tables import Event
from metamorph.adapters.repository import EventSourceRepository
from metamorph.domain.model import BaseEvent

fake = Faker()


@pytest.mark.parametrize(
    "base_event, total_events",
    [
        (
            BaseEvent(
                event_id=fake.uuid4(),
                name=f"test-event-{fake.word()}-v0",
                created_at=datetime.now(),
                topic_target=f"test-topic-{fake.word()}",
                payload={fake.word(): f"{fake.pyint()}"},
                is_processed=False,
            ),
            total_events,
        )
        for total_events in range(1, 11)
    ],
)
def test_add_event(base_event, total_events, create_database):
    repository = EventSourceRepository()
    key = repository.add(base_event=base_event)
    created_at = key[0]["created_at"]
    assert Event.count().where(Event.created_at == created_at).run_sync() == 1
    assert Event.count().run_sync() == total_events
