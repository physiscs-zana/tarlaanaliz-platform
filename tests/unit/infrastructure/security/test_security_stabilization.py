# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

import pytest

from src.infrastructure.security.encryption import EncryptionService
from src.infrastructure.security.jwt_handler import JWTHandler, JWTSettings
from src.infrastructure.security.query_pattern_analyzer import QueryPatternAnalyzer
from src.infrastructure.security.rate_limit_config import parse_rate_limit_rules

pytestmark = pytest.mark.unit


def test_jwt_issue_and_verify_roundtrip() -> None:
    handler = JWTHandler(JWTSettings(secret_key="secret", access_token_ttl_minutes=5))

    token = handler.issue_access_token(subject="user-1", claims={"role": "pilot"})
    decoded = handler.verify_token(token)

    assert decoded["sub"] == "user-1"
    assert decoded["role"] == "pilot"


def test_encryption_roundtrip() -> None:
    service = EncryptionService(EncryptionService.generate_key())

    cipher = service.encrypt("sensitive")

    assert service.decrypt(cipher) == "sensitive"


def test_rate_limit_parser_and_query_scan() -> None:
    rules = parse_rate_limit_rules(["/api/v1/auth=10/60", "/api/v1/results=120/60"])
    analyzer = QueryPatternAnalyzer()

    assert len(rules) == 2
    assert rules[0].requests == 10
    assert analyzer.scan("SELECT * FROM users WHERE id = 1").is_suspicious is False
    assert analyzer.scan("SELECT * FROM users WHERE id = 1 OR 1=1").is_suspicious is True


def test_jwt_verify_rejects_invalid_audience() -> None:
    handler = JWTHandler(JWTSettings(secret_key="secret", access_token_ttl_minutes=5, audience="tarlaanaliz-api"))

    # SEC-FIX: PyJWT doesn't allow overriding aud via claims like jose did.
    # Create a token with a different handler that has a different audience.
    wrong_handler = JWTHandler(JWTSettings(secret_key="secret", access_token_ttl_minutes=5, audience="different-audience"))
    token = wrong_handler.issue_access_token(subject="user-1")

    with pytest.raises(ValueError, match="Invalid JWT token"):
        handler.verify_token(token)
