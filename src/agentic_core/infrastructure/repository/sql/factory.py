from agentic_core.infrastructure.repository.sql.adapter import SQLExpressionHandler
from agentic_core.infrastructure.repository.sql_handler import SQLHandler, DEFAULT_DIALECT


class SQLHandlerFactory:
    def __call__(self, expression: str, dialect: str = DEFAULT_DIALECT) -> SQLHandler:
        return SQLExpressionHandler(expression, dialect)
