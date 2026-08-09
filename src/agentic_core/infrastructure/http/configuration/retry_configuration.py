from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class RetrySettings:
    retry_count: int = 4
    retry_delay: float = 5
    retry_on: tuple[type[Exception], ...] = (Exception,)

    def __post_init__(self) -> Optional[Exception]:
        if not self.retry_on:
            raise RuntimeError("retry_on cannot be empty")
