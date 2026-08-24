from agentic_core.infrastructure.authentication.model.basic_auth import BasicAuth
from agentic_core.infrastructure.authentication.model.no_auth import NoAuth
from agentic_core.infrastructure.authentication.model.token_auth import TokenAuth

AuthTyping = NoAuth | TokenAuth | BasicAuth
