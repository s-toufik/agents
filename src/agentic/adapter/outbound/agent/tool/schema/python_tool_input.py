from pydantic import BaseModel, Field, PrivateAttr


class PythonToolInput(BaseModel):
    _call_id: str = PrivateAttr()
    code: str = Field(..., description="Python source code to run in a sandbox.")

    @property
    def call_id(self):
        return self._call_id

    @call_id.setter
    def call_id(self, value):
        self._call_id = value
