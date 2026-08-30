from dataclasses import FrozenInstanceError

import pytest

from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.authentication.model.token_auth import TokenAuth


def test_basic_auth_defaults_type_to_basic():
    auth = BasicAuth(username="u", password="p")

    assert auth.username == "u"
    assert auth.password == "p"
    assert auth.type == AuthType.basic


def test_basic_auth_with_explicit_type():
    auth = BasicAuth(username="u", password="p", type=AuthType.basic)

    assert auth.type == AuthType.basic


def test_basic_auth_is_frozen():
    auth = BasicAuth(username="u", password="p")

    with pytest.raises(FrozenInstanceError):
        auth.username = "other"


def test_no_auth_defaults_type_to_none():
    auth = NoAuth()

    assert auth.type == AuthType.none


def test_no_auth_with_explicit_type():
    auth = NoAuth(type=AuthType.none)

    assert auth.type == AuthType.none


def test_token_auth_defaults_type_to_token():
    auth = TokenAuth(key_name="X-Api-Key", key_value="secret")

    assert auth.key_name == "X-Api-Key"
    assert auth.key_value == "secret"
    assert auth.type == AuthType.token


def test_token_auth_with_explicit_type():
    auth = TokenAuth(key_name="X-Api-Key", key_value="secret", type=AuthType.token)

    assert auth.type == AuthType.token


def test_auth_type_values():
    assert AuthType.token.value == "token"
    assert AuthType.basic.value == "basic"
    assert AuthType.none.value == "none"
