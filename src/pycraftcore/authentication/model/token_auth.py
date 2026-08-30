from dataclasses import dataclass, field

from .auth_type import AuthType


@dataclass(frozen=True, slots=True)
class TokenAuth:
    key_name: str
    key_value: str
    type: AuthType = field(default_factory=AuthType.token)
