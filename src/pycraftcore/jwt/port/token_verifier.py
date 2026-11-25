from typing import Protocol, runtime_checkable

from pycraftcore.jwt.schema.token_claims import TokenClaims


@runtime_checkable
class TokenVerifier(Protocol):
    def verify(self, token: str) -> TokenClaims: ...
