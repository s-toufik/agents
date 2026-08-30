from agentic_core.infrastructure.application_configuration.model.connector import DatabaseConnector
from agentic_core.infrastructure.repository.sqlite.schema import SqliteConnector


class SqliteSettingsMapper:
    def __init__(self, database_connector: DatabaseConnector):
        self._database_connector = database_connector

    def __call__(self) -> SqliteConnector:
        return SqliteConnector(
            path=self._database_connector.host,
            default_name=self._database_connector.default_name,
            max_pool_size=self._database_connector.pool.get("max", 1)
        )
