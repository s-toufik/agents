from enum import Enum


class ReflectionAction(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"
