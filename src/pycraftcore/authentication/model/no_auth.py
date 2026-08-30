from dataclasses import dataclass, field

from .auth_type import AuthType


@dataclass(frozen=True, slots=True)
class NoAuth:
    type: AuthType = field(default_factory=AuthType.none)
