from typing import cast
from sqlglot import parse, ErrorLevel, Expr, errors, exp

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


class SQLExpressionHandler:

    def __init__(self, expression: str, dialect: str = "sqlite"):
        self._expression = expression
        self._dialect = dialect

    def parse(self) -> list[Expr]:
        try:
            expressions: list[Expr | None] = parse(
                self._expression,
                dialect=self._dialect,
                error_level=ErrorLevel.RAISE,
            )

            if not all(expressions):
                raise ValueError("Empty SQL expression detected")

            return cast(list[Expr], expressions)

        except errors.SqlglotError as exception:
            raise ValueError(
                f"Invalid SQL: {exception}"
            ) from exception

    def validate_read_only(self, expressions: list[Expr] | None = None):
        expressions = expressions or self.parse()

        for expression in expressions:
            for node in expression.walk():
                if isinstance(node, FORBIDDEN_STATEMENTS):
                    raise ValueError(
                        f"{type(node).__name__} is not allowed"
                    )

    def transpile(self, expressions: list[Expr] | None = None) -> str:
        expressions = expressions or self.parse()

        self.validate_read_only(expressions)

        return ";\n".join(
            expression.sql(dialect="sqlite")
            for expression in expressions
        )