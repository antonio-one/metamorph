import pytest

from database.tables import Event


@pytest.mark.order("first")
def test_database_table_is_empty(create_database):
    assert Event.count().run_sync() == 0


@pytest.mark.order("last")
def test_database_table_has_rows(create_database):
    assert Event.count().run_sync() == 10
