from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from pycraftcore.jwt.exception.invalid_token_exception import InvalidTokenException
from pycraftcore.jwt.schema.token_claims import TokenClaims

_MINIMUM_KEY_BYTES: dict[str, int] = {"HS256": 32, "HS384": 48, "HS512": 64}


class PyJwtTokens:
    def __init__(
        self,
        key: str,
        algorithm: str = "HS256",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if algorithm not in _MINIMUM_KEY_BYTES:
            raise ValueError(f"JWT algorithm must be one of {', '.join(_MINIMUM_KEY_BYTES)}")
        if len(key.encode()) < _MINIMUM_KEY_BYTES[algorithm]:
            raise ValueError(
                f"JWT key must be at least {_MINIMUM_KEY_BYTES[algorithm]} bytes for {algorithm}"
            )
        self._key = key
        self._algorithm = algorithm
        self._clock = clock

    def issue(self, subject: str, lifetime: timedelta | None) -> str:
        if not subject.strip():
            raise ValueError("a token needs a subject")
        if lifetime is not None and lifetime <= timedelta(0):
            raise ValueError(
                "a token's lifetime must be positive, or None for a token that never expires"
            )
        now: datetime = self._clock()
        claims: dict[str, Any] = {"sub": subject, "iat": int(now.timestamp())}
        if lifetime is not None:
            claims["exp"] = int((now + lifetime).timestamp())
        return jwt.encode(claims, self._key, algorithm=self._algorithm)

    def verify(self, token: str) -> TokenClaims:
        try:
            claims: dict[str, Any] = jwt.decode(
                token, self._key, algorithms=[self._algorithm], options={"require": ["sub", "iat"]}
            )
        except jwt.ExpiredSignatureError as error:
            raise InvalidTokenException("the token has expired") from error
        except jwt.InvalidTokenError as error:
            raise InvalidTokenException(f"the token is not valid: {error}") from error
        expires: Any = claims.get("exp")
        return TokenClaims(
            subject=claims["sub"],
            issued_at=datetime.fromtimestamp(claims["iat"], UTC),
            expires_at=datetime.fromtimestamp(expires, UTC) if expires is not None else None,
        )
