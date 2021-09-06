from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from metamorph.constants import (
    METAMORPH_DATABASE_HOST,
    METAMORPH_DATABASE_NAME,
    METAMORPH_DATABASE_PASSWORD,
    METAMORPH_DATABASE_PORT,
    METAMORPH_DATABASE_USER,
)

DB = PostgresEngine(
    config={
        "database": METAMORPH_DATABASE_NAME,
        "user": METAMORPH_DATABASE_USER,
        "password": METAMORPH_DATABASE_PASSWORD,
        "host": METAMORPH_DATABASE_HOST,
        "port": METAMORPH_DATABASE_PORT,
    }
)


APP_REGISTRY = AppRegistry(apps=["database.metamorph"])
