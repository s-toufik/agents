from enum import Enum


class MessageStreamType(Enum):
    TOKEN = "token"
    COMPLETE = "complete"
    ERROR = "error"
    FINAL = "final"
