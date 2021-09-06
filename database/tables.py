from piccolo.columns import JSON, Boolean, Timestamp, Varchar
from piccolo.table import Table


class Event(Table):
    event_id = Varchar(length=128, primary_key=True)
    name = Varchar(length=128)
    created_at = Timestamp(primary_key=True)
    topic_target = Varchar(length=128)
    payload = JSON()
    is_processed = Boolean(default=False)


class Raw(Table):
    """
    Hack used to execute freestyle sql statements
    """

    pass
