from datetime import UTC, datetime, timedelta

import jwt
import pytest

from pycraftcore.jwt import InvalidTokenException, TokenClaims, TokenIssuer, TokenVerifier
from pycraftcore.jwt.adapter import PyJwtTokens

KEY = "k" * 32
NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def tokens(key: str = KEY, now: datetime = NOW, algorithm: str = "HS256") -> PyJwtTokens:
    return PyJwtTokens(key, algorithm=algorithm, clock=lambda: now)


def test_the_adapter_is_both_an_issuer_and_a_verifier() -> None:
    assert isinstance(tokens(), TokenIssuer)
    assert isinstance(tokens(), TokenVerifier)


def test_a_token_carries_its_subject_and_expires_after_its_lifetime() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    adapter = tokens(now=now)

    claims = adapter.verify(adapter.issue("toufik", timedelta(hours=5)))

    assert claims == TokenClaims("toufik", issued_at=now, expires_at=now + timedelta(hours=5))
    assert not claims.never_expires


def test_a_token_without_a_lifetime_never_expires() -> None:
    adapter = tokens()

    token = adapter.issue("agent-runtime", None)

    assert "exp" not in jwt.decode(token, options={"verify_signature": False})
    assert adapter.verify(token).never_expires


def test_an_expired_token_is_refused() -> None:
    token = tokens(now=datetime(2020, 1, 1, tzinfo=UTC)).issue("toufik", timedelta(hours=5))

    with pytest.raises(InvalidTokenException, match="expired"):
        tokens().verify(token)


@pytest.mark.parametrize(
    "token",
    [
        PyJwtTokens("x" * 32).issue("toufik", timedelta(hours=1)),
        jwt.encode({"sub": "toufik", "iat": 1}, key="", algorithm="none"),
        jwt.encode({"iat": 1}, KEY, algorithm="HS256"),
        "not.a.token",
        "",
    ],
    ids=["other key", "unsigned", "no subject", "malformed", "empty"],
)
def test_a_forged_or_malformed_token_is_refused(token: str) -> None:
    with pytest.raises(InvalidTokenException, match="not valid"):
        tokens().verify(token)


@pytest.mark.parametrize(
    ("key", "algorithm", "message"),
    [
        ("k" * 31, "HS256", "at least 32 bytes for HS256"),
        ("k" * 47, "HS384", "at least 48 bytes for HS384"),
        (KEY, "RS256", "must be one of HS256, HS384, HS512"),
    ],
)
def test_a_key_too_short_for_its_algorithm_is_refused(key, algorithm, message) -> None:
    with pytest.raises(ValueError, match=message):
        PyJwtTokens(key, algorithm=algorithm)


@pytest.mark.parametrize(
    ("subject", "lifetime", "message"),
    [(" ", None, "needs a subject"), ("toufik", timedelta(0), "must be positive")],
)
def test_a_token_that_cannot_be_issued_is_refused(subject, lifetime, message) -> None:
    with pytest.raises(ValueError, match=message):
        tokens().issue(subject, lifetime)
