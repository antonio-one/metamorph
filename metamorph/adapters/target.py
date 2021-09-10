from metamorph.adapters.base import BaseRepository
from metamorph.domain.model import BaseEvent


class EventTargetRepository(BaseRepository):
    def add(self, event: BaseEvent):
        """"""

    def delete(self, *args, **kwargs):
        return NotImplementedError

    def get(self):
        """"""

    def update(self, *args, **kwargs):
        return NotImplementedError
