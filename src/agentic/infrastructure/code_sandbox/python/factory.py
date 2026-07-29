from string import Template
from typing import Optional

from agentic.infrastructure.code_sandbox.code import Code, TIMEOUT, MAX_MEMORY_MB
from agentic.infrastructure.code_sandbox.python.adapter import SafeCode


class SafeCodeFactory:
    def __call__(
        self,
        code: str,
        code_template: Optional[Template] = None,
        code_timeout: Optional[int] = TIMEOUT,
        max_memory_mb: Optional[int] = MAX_MEMORY_MB,
    ) -> Code:
        return SafeCode(
            code=code,
            code_template=code_template,
            code_timeout=code_timeout,
            max_memory_mb=max_memory_mb,
        )
