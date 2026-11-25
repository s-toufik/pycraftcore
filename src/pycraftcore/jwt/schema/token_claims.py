from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TokenClaims:
    subject: str
    issued_at: datetime
    expires_at: datetime | None = None

    @property
    def never_expires(self) -> bool:
        return self.expires_at is None
