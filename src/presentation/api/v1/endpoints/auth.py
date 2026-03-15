# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: Telefon + 6 haneli PIN (sabit uzunluk, yalnızca rakam).
# KR-050: Brute force koruması — 16 hata → 30 dakika kilit (SC-SEC-02).
# KR-081: contract-first auth; no email/TCKN/OTP.
# SC-SEC-02: 16 başarısız giriş → 30 dakika kilitleme.

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from src.infrastructure.security.jwt_handler import JWTHandler, JWTSettings

LOGGER = logging.getLogger("api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

# KR-050: Sabit 6 haneli sayısal PIN (v1.2.0 — eski: 4-12 chars)
_PIN_LENGTH = 6
_MAX_FAILED_LOGIN_ATTEMPTS = 16  # KR-050 / SC-SEC-02: 16 hata → 30 dakika kilit
_LOCKOUT_DURATION_SECONDS = 30 * 60  # 30 dakika


class PhonePinLoginRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    pin: str = Field(min_length=_PIN_LENGTH, max_length=_PIN_LENGTH)

    @field_validator("pin")
    @classmethod
    def pin_must_be_digits(cls, v: str) -> str:
        """KR-050: PIN tam olarak 6 haneli sayı olmalı."""
        if not v.isdigit():
            raise ValueError("PIN yalnızca rakamlardan oluşmalıdır (KR-050)")
        return v


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    subject: str
    phone_verified: bool = True


class AuthRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=8)


class PhonePinAuthService(Protocol):
    def login(self, phone: str, pin: str) -> AuthTokenResponse: ...

    def refresh(self, refresh_token: str) -> AuthTokenResponse: ...


@dataclass(slots=True)
class _LoginAttemptRecord:
    fail_count: int = 0
    locked_until: float = 0.0


# SC-SEC-02: In-memory brute-force tracking (per-phone).
_login_attempts: dict[str, _LoginAttemptRecord] = {}


def _get_jwt_handler() -> JWTHandler:
    from src.presentation.api.settings import settings

    return JWTHandler(JWTSettings(secret_key=settings.jwt.secret))


@dataclass(slots=True)
class _InMemoryPhonePinAuthService:
    _jwt_handler: JWTHandler = field(default_factory=_get_jwt_handler)

    def _check_lockout(self, phone: str) -> None:
        """SC-SEC-02: 16 başarısız giriş → 30 dakika kilit."""
        record = _login_attempts.get(phone)
        if record is None:
            return
        if record.locked_until > time.time():
            retry_after = int(record.locked_until - time.time()) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Hesap kilitli. {retry_after} saniye sonra tekrar deneyin.",
                headers={"Retry-After": str(retry_after)},
            )
        # Kilitleme süresi dolmuşsa sayacı sıfırla
        if record.locked_until > 0 and record.locked_until <= time.time():
            record.fail_count = 0
            record.locked_until = 0.0

    def _record_failure(self, phone: str) -> None:
        """SC-SEC-02: Başarısız girişi kaydet, gerekirse kilitle."""
        record = _login_attempts.setdefault(phone, _LoginAttemptRecord())
        record.fail_count += 1
        if record.fail_count >= _MAX_FAILED_LOGIN_ATTEMPTS:
            record.locked_until = time.time() + _LOCKOUT_DURATION_SECONDS

    def _record_success(self, phone: str) -> None:
        """Başarılı girişte sayacı sıfırla."""
        _login_attempts.pop(phone, None)

    def login(self, phone: str, pin: str) -> AuthTokenResponse:
        # SC-SEC-02: Kilitleme kontrolü
        self._check_lockout(phone)

        # KR-081: explicit auth contract; no email/TCKN/OTP fields accepted.
        # KR-050: PIN tam 6 haneli sayısal.
        # SEC-FIX: Hardcoded credentials kaldırıldı. Gerçek kullanıcı doğrulaması
        # veritabanı üzerinden yapılmalıdır. Bu stub, user_repo entegrasyonuna kadar
        # sadece env-tabanlı test credentials ile çalışır.
        import os

        _test_phone = os.getenv("AUTH_TEST_PHONE")
        _test_pin = os.getenv("AUTH_TEST_PIN")
        if not _test_phone or not _test_pin:
            LOGGER.error("AUTH_TEST_PHONE/AUTH_TEST_PIN env vars not set — login disabled until user_repo is integrated")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service not configured",
            )

        if phone != _test_phone or pin != _test_pin:
            self._record_failure(phone)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        self._record_success(phone)
        # KR-050: Gerçek signed JWT token üretimi
        access_token = self._jwt_handler.issue_access_token(
            subject="user-1",
            claims={"phone": phone, "phone_verified": True},
        )
        return AuthTokenResponse(access_token=access_token, subject="user-1")

    def refresh(self, refresh_token: str) -> AuthTokenResponse:
        # Refresh token doğrulama
        try:
            payload = self._jwt_handler.verify_token(refresh_token)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized") from None
        subject = str(payload.get("sub", ""))
        access_token = self._jwt_handler.issue_access_token(
            subject=subject,
            claims={"phone_verified": True},
        )
        return AuthTokenResponse(access_token=access_token, subject=subject)


# ---------------------------------------------------------------------------
# KR-050 / SC-SEC-02: Brute force lockout — process-local store
# ---------------------------------------------------------------------------
@dataclass
class LoginAttemptTracker:
    """Tracks failed login attempts per phone number for brute force protection.

    KR-050: 16 failed attempts → 30 minute lockout.
    SC-SEC-02: Brute force 16 fail → 30 min lock.
    """

    _lock: threading.Lock = field(default_factory=threading.Lock)
    _attempts: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    _lockouts: dict[str, float] = field(default_factory=dict)

    def is_locked(self, phone: str) -> tuple[bool, int]:
        """Check if phone is locked out. Returns (is_locked, retry_after_seconds)."""
        with self._lock:
            lockout_until = self._lockouts.get(phone)
            if lockout_until is not None:
                now = time.monotonic()
                if now < lockout_until:
                    return True, max(1, int(lockout_until - now))
                # Lockout expired — clear state
                del self._lockouts[phone]
                self._attempts.pop(phone, None)
            return False, 0

    def record_failure(self, phone: str) -> tuple[bool, int]:
        """Record a failed login. Returns (is_now_locked, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            attempts = self._attempts[phone]
            # Prune old attempts outside lockout window
            window_start = now - _LOCKOUT_DURATION_SECONDS
            self._attempts[phone] = [t for t in attempts if t > window_start]
            self._attempts[phone].append(now)

            if len(self._attempts[phone]) >= _MAX_FAILED_LOGIN_ATTEMPTS:
                self._lockouts[phone] = now + _LOCKOUT_DURATION_SECONDS
                LOGGER.warning(
                    "AUTH.LOCKOUT",
                    extra={
                        "event": "AUTH.LOCKOUT",
                        "phone_hash": phone[-4:],
                        "attempts": len(self._attempts[phone]),
                    },
                )
                return True, _LOCKOUT_DURATION_SECONDS
            return False, 0

    def record_success(self, phone: str) -> None:
        """Clear attempts on successful login."""
        with self._lock:
            self._attempts.pop(phone, None)
            self._lockouts.pop(phone, None)


_LOGIN_TRACKER = LoginAttemptTracker()


def get_phone_pin_auth_service() -> PhonePinAuthService:
    return _InMemoryPhonePinAuthService()


@router.post("/phone-pin/login", response_model=AuthTokenResponse)
def phone_pin_login(
    payload: PhonePinLoginRequest,
    response: Response,
    service: PhonePinAuthService = Depends(get_phone_pin_auth_service),
) -> AuthTokenResponse:
    # KR-050 / SC-SEC-02: Check lockout before attempting login
    locked, retry_after = _LOGIN_TRACKER.is_locked(payload.phone)
    if locked:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    try:
        result = service.login(phone=payload.phone, pin=payload.pin)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            # Record failed attempt
            now_locked, lockout_retry = _LOGIN_TRACKER.record_failure(payload.phone)
            if now_locked:
                response.headers["Retry-After"] = str(lockout_retry)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please try again later.",
                ) from exc
        raise

    # Success — clear attempts
    _LOGIN_TRACKER.record_success(payload.phone)
    return result


@router.post("/phone-pin/refresh", response_model=AuthTokenResponse)
def phone_pin_refresh(
    payload: AuthRefreshRequest, service: PhonePinAuthService = Depends(get_phone_pin_auth_service)
) -> AuthTokenResponse:
    return service.refresh(refresh_token=payload.refresh_token)


@router.get("/me")
def me(request: Request) -> dict[str, str | bool]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return {
        "subject": str(getattr(user, "subject", "")),
        "phone_verified": bool(getattr(user, "phone_verified", False)),
    }
