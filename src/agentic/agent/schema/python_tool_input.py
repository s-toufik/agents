from pydantic import BaseModel, Field


class PythonToolInput(BaseModel):
    code: str = Field(..., description="Python source code to run in a sandbox.")