from pydantic import BaseModel, PrivateAttr


class ToolInput(BaseModel):
    _call_id: str = PrivateAttr()

    @property
    def call_id(self) -> str:
        return self._call_id

    @call_id.setter
    def call_id(self, value: str) -> None:
        self._call_id = value
