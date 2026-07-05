from pydantic import BaseModel, Field


class SQLToolInput(BaseModel):
    query:   str = Field(...,        description="SQL query to execute.")
    dialect: str = Field("oracle",   description="sqlglot source dialect.")