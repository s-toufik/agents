from typing import cast, Optional

from agentic.infrastructure.logger.port.logger import Logger


def create_logger(logger: Optional[Logger]) -> Logger:
    if logger is None:
        from logging import getLogger

        return cast(Logger, getLogger(__name__))
    return logger
