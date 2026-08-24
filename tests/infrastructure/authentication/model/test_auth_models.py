import pytest

from agentic_core.infrastructure.authentication.model.auth_type import AuthType
from agentic_core.infrastructure.authentication.model.basic_auth import BasicAuth
from agentic_core.infrastructure.authentication.model.no_auth import NoAuth
from agentic_core.infrastructure.authentication.model.token_auth import TokenAuth


def test_basic_auth_with_explicit_type():
    auth = BasicAuth(username="u", password="p", type=AuthType.basic)

    assert auth.type == AuthType.basic


def test_no_auth_with_explicit_type():
    auth = NoAuth(type=AuthType.none)

    assert auth.type == AuthType.none


def test_token_auth_with_explicit_type():
    auth = TokenAuth(key_name="X-Api-Key", key_value="secret", type=AuthType.token)

    assert auth.type == AuthType.token


def test_basic_auth_default_type_is_broken():
    """Regression test documenting a real bug: `field(default_factory=AuthType.basic)`
    stores the enum *member* as the factory, and calling a member raises TypeError
    instead of yielding AuthType.basic. Omitting `type=` currently fails outright."""
    with pytest.raises(TypeError):
        BasicAuth(username="u", password="p")


def test_no_auth_default_type_is_broken():
    with pytest.raises(TypeError):
        NoAuth()


def test_token_auth_default_type_is_broken():
    with pytest.raises(TypeError):
        TokenAuth(key_name="X-Api-Key", key_value="secret")
