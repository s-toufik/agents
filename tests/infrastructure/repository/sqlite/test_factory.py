import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_core.infrastructure.repository.sqlite.factory import SQLiteRepositoryFactory
from agentic_core.infrastructure.repository.sqlite.schema import SqliteConnector


@pytest.mark.asyncio
async def test_connection_creates_directory_and_memoizes_client(tmp_path):
    db_dir = tmp_path / "data"
    settings = SqliteConnector(path=str(db_dir), default_name="main")
    factory = SQLiteRepositoryFactory(settings)
    fake_client = MagicMock()

    with patch(
        "agentic_core.infrastructure.repository.sqlite.factory.connect",
        AsyncMock(return_value=fake_client),
    ) as mock_connect:
        first = await factory.connection()
        second = await factory.connection()

    assert db_dir.exists()
    assert first is fake_client
    assert second is fake_client
    mock_connect.assert_awaited_once()
    assert mock_connect.call_args[0][0] == str(db_dir / "main.db")


@pytest.mark.asyncio
async def test_connection_does_not_create_directory_when_it_already_exists(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main")
    factory = SQLiteRepositoryFactory(settings)

    with patch(
        "agentic_core.infrastructure.repository.sqlite.factory.connect",
        AsyncMock(return_value=MagicMock()),
    ):
        await factory.connection()

    assert tmp_path.exists()


@pytest.mark.asyncio
async def test_connect_returns_sqlite_repository_wrapping_the_connection(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main")
    factory = SQLiteRepositoryFactory(settings)
    fake_client = MagicMock()

    with patch(
        "agentic_core.infrastructure.repository.sqlite.factory.connect",
        AsyncMock(return_value=fake_client),
    ):
        repository = await factory.connect()

    assert repository._client is fake_client


@pytest.mark.asyncio
async def test_disconnect_closes_client_and_is_idempotent(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main")
    factory = SQLiteRepositoryFactory(settings)
    fake_client = MagicMock()
    fake_client.close = AsyncMock()

    with patch(
        "agentic_core.infrastructure.repository.sqlite.factory.connect",
        AsyncMock(return_value=fake_client),
    ):
        await factory.connection()

    await factory.disconnect()
    fake_client.close.assert_awaited_once()

    await factory.disconnect()
    fake_client.close.assert_awaited_once()
