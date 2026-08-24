import pytest
from unittest.mock import MagicMock

from agentic_core.infrastructure.application_configuration.adapter.load_configuration import (
    LoadConfiguration,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    LoadConfiguration._instance = None
    yield
    LoadConfiguration._instance = None


def test_load_caches_after_first_successful_read():
    reader = MagicMock()
    reader.read.return_value = "config-v1"
    logger = MagicMock()
    loader = LoadConfiguration(reader, logger)

    first = loader.load()
    second = loader.load()

    assert first == "config-v1"
    assert second == "config-v1"
    reader.read.assert_called_once()


def test_load_returns_cached_none_and_logs_when_reader_raises():
    reader = MagicMock()
    reader.read.side_effect = RuntimeError("bad config")
    logger = MagicMock()
    loader = LoadConfiguration(reader, logger)

    result = loader.load()

    assert result is None
    logger.critical.assert_called_once()


def test_reload_always_re_reads_and_overwrites_cache():
    reader = MagicMock()
    reader.read.side_effect = ["config-v1", "config-v2"]
    logger = MagicMock()
    loader = LoadConfiguration(reader, logger)

    loader.load()
    reloaded = loader.reload()

    assert reloaded == "config-v2"
    assert reader.read.call_count == 2


def test_is_a_singleton_across_construction_calls():
    reader = MagicMock()
    logger = MagicMock()

    first = LoadConfiguration(reader, logger)
    second = LoadConfiguration(reader, logger)

    assert first is second
