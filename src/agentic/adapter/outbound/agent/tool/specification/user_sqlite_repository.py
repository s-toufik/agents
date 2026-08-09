from pydantic import BaseModel

from agentic.adapter.outbound.agent.tool.schema.sql_tool_input import SQLToolInput
from agentic_core.infrastructure.repository.sql_handler import FORBIDDEN_STATEMENTS

name: str = "users_tables"
dialect: str = "sqlite"
description: str = (
    f"Execute SQL queries against the service db that contains the service information such as users dash bord, payment info ..."
    f"Defaults to {dialect} dialect."
    f"Forbidden operations are:\n {', '.join([item.__name__ for item in FORBIDDEN_STATEMENTS])}"
)
args_schema: type[BaseModel] = SQLToolInput
