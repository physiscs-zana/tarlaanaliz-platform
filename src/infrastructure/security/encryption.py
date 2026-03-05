# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-066: PII simetrik şifreleme/çözme adaptörü.

"""Symmetric encryption adapter."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    """Fernet based encrypt/decrypt adapter."""

    def __init__(self, key: bytes) -> None:
        self._fernet = Fernet(key)

    @staticmethod
    def generate_key() -> bytes:
        return Fernet.generate_key()

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            plain = self._fernet.decrypt(token.encode("utf-8"))
        except InvalidToken as exc:
            raise ValueError("Invalid encrypted payload") from exc
        return plain.decode("utf-8")
