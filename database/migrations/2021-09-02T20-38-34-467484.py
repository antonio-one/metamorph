from piccolo.apps.migrations.auto import MigrationManager

from database.tables import Raw

ID = "2021-09-02T20:38:34:467484"
VERSION = "0.43.0"
DESCRIPTION = ""
SQL_COMMAND = """
CREATE TABLE event (
    "event_id" varchar(36) NOT NULL,
    "name" VARCHAR(128) NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT current_timestamp,
    "topic_target" VARCHAR(128) NOT NULL,
    "payload" JSON NOT NULL,
    "is_processed" BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY(created_at, event_id)
)
"""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="metamorph", description=DESCRIPTION
    )

    def run():
        Raw.raw(sql=SQL_COMMAND).run_sync()

    manager.add_raw(run)

    return manager
