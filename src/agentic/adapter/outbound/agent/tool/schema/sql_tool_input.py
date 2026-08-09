from pydantic import BaseModel, Field, PrivateAttr


class SQLToolInput(BaseModel):
    _call_id: str = PrivateAttr()
    query: str = Field(..., description="SQL query to execute.")
    dialect: str = Field(..., description="sqlglot source dialect.")

    @property
    def call_id(self):
        return self._call_id

    @call_id.setter
    def call_id(self, value):
        self._call_id = value
