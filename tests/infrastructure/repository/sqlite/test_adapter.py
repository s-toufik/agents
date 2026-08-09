import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic_core.infrastructure.repository.sqlite.adapter import SQLiteRepository


@pytest.fixture
def fake_cursor():
    cursor = MagicMock()

    cursor.description = ["id", "name"]

    cursor.fetchall = AsyncMock(
        return_value=[
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Alice"},
        ]
    )

    return cursor


@pytest.fixture
def fake_connection(fake_cursor):
    connection = MagicMock()

    connection.execute = AsyncMock(return_value=fake_cursor)

    return connection


@pytest.fixture
def repository(fake_connection):
    return SQLiteRepository(fake_connection)


@pytest.mark.asyncio
async def test_execute_returns_rows_as_dict(
    repository,
    fake_connection,
):
    # Act
    result = await repository.execute("SELECT * FROM users")

    # Assert
    fake_connection.execute.assert_called_once_with("SELECT * FROM users", ())

    assert result == [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Alice"},
    ]
