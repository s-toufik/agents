from dataclasses import dataclass
from string import Template
from typing import Protocol, Optional

TIMEOUT: int = 10
MAX_MEMORY_MB: int = 256


@dataclass
class CodeStdout:
    stdout: str
    stderr: str


class CodeFactory(Protocol):
    def __call__(
        self,
        code: str,
        code_template: Optional[Template],
        code_timeout: Optional[int],
        max_memory_mb: Optional[int],
    ) -> Code: ...


class Code(Protocol):
    async def execute(self) -> CodeStdout: ...
