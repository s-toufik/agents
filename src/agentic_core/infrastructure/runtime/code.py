from string import Template
from typing import Protocol, Optional

from agentic_core.infrastructure.runtime.python.schema import CodeStdout


class CodeFactory(Protocol):
    def __call__(
        self,
        code: str,
        code_template: Optional[Template] = None
    ) -> Code: ...


class Code(Protocol):
    async def execute(self) -> CodeStdout: ...
