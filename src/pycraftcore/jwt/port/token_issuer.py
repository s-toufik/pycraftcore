from datetime import timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenIssuer(Protocol):
    def issue(self, subject: str, lifetime: timedelta | None) -> str: ...
