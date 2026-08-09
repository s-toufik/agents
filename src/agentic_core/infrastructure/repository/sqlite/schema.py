from pydantic import BaseModel


class SqliteConnector(BaseModel):
    path: str
    default_name: str
