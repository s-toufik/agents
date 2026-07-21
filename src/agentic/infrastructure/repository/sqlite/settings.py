from agentic.infrastructure.repository.sqlite.schema import SqliteConnector


class SqliteSettings:
    def __init__(self, connector: SqliteConnector):
        self._connector = connector

    @property
    def database_path(self):
        return self._connector.path

    @property
    def database_name(self):
        return self._connector.default_name
