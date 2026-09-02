from pycraftcore.query_language.constants import FORBIDDEN_SQL_EXPRESSIONS

from agentic.adapter.outbound.agent_tool.schema.sql_tool_input import SQLToolInput

name: str = "users_tables"
dialect: str = "sqlite"
description: str = (
    f"Execute SQL queries against the service db that contains the service information such as users dash bord, payment info ..."
    f"You must return the required arguments"
    f"Defaults to {dialect} dialect."
    f"Forbidden operations are:\n {', '.join([item.__name__ for item in FORBIDDEN_SQL_EXPRESSIONS])}"
)
args_schema: type[SQLToolInput] = SQLToolInput
