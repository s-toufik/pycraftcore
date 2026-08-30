from dataclasses import dataclass, field

from .auth_type import AuthType


@dataclass(frozen=True, slots=True)
class BasicAuth:
    username: str
    password: str
    type: AuthType = field(default=AuthType.basic)
