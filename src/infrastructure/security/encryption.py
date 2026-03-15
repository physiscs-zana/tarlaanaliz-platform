# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-066: PII simetrik şifreleme/çözme adaptörü.
# SEC-FIX: Fernet (AES-128-CBC) → AES-256-GCM (KVKK uyumlu)

"""AES-256-GCM symmetric encryption adapter (KVKK compliant)."""

from __future__ import annotations

import base64
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_NONCE_SIZE = 12  # 96-bit nonce for AES-GCM (NIST recommended)
_KEY_SIZE = 32  # 256-bit key


class EncryptionService:
    """AES-256-GCM encrypt/decrypt adapter (KVKK AES-256 requirement)."""

    def __init__(self, key: bytes) -> None:
        if len(key) != _KEY_SIZE:
            raise ValueError(f"Key must be exactly {_KEY_SIZE} bytes (AES-256), got {len(key)}")
        self._aesgcm = AESGCM(key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a cryptographically secure 256-bit key."""
        return AESGCM.generate_key(256)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext and return base64-encoded nonce+ciphertext."""
        nonce = os.urandom(_NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Prepend nonce to ciphertext for storage
        return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypt base64-encoded nonce+ciphertext token."""
        try:
            raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        except Exception as exc:
            raise ValueError("Invalid encrypted payload — base64 decode failed") from exc

        if len(raw) < _NONCE_SIZE + 1:
            raise ValueError("Invalid encrypted payload — too short")

        nonce = raw[:_NONCE_SIZE]
        ciphertext = raw[_NONCE_SIZE:]

        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as exc:
            raise ValueError("Invalid encrypted payload — decryption failed") from exc

        return plaintext.decode("utf-8")
