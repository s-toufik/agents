from enum import Enum


class AgentMessageStatus(Enum):
    TOKENS = "tokens"
    COMPLETE = "complete"
    ERROR = "error"
    END = "end"
