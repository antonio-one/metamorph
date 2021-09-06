from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class BaseEvent:
    event_id: str
    name: str
    created_at: datetime
    topic_target: str
    payload: Dict[str, Any]
    is_processed: bool

    def to_dict(self):
        return self.__dict__


@dataclass
class KafkaBroker:
    bootstrap_server: List[str]
