from dataclasses import dataclass, field

from .auth_type import AuthType


@dataclass(frozen=True, slots=True)
class TokenAuth:
    key_name: str
    key_value: str = field(repr=False)
    type: AuthType = field(default=AuthType.token)
