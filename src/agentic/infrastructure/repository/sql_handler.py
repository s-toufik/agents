from typing import Protocol, TypeVar
from sqlglot import exp


T = TypeVar("T")

FORBIDDEN_STATEMENTS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Merge,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Attach,
    exp.Detach,
)

DEFAULT_DIALECT = "sqlite"


class SQLFactory(Protocol):
    def __call__(self, expression: str, dialect: str = DEFAULT_DIALECT) -> SQLHandler: ...


class SQLHandler(Protocol):
    def transpile(self, expressions: T = None) -> str: ...
