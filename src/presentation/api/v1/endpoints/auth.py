# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: Telefon + 6 haneli PIN (sabit uzunluk, yalnızca rakam).
# KR-050: Brute force koruması — 16 hata → 30 dakika kilit (SC-SEC-02).
# KR-081: contract-first auth; no email/TCKN/OTP.
# SC-SEC-02: 16 başarısız giriş → 30 dakika kilitleme.

from __future__ import annotations

import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Protocol

import bcrypt
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
    async def login(self, phone: str, pin: str) -> AuthTokenResponse: ...

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

    async def login(self, phone: str, pin: str) -> AuthTokenResponse:
        self._check_lockout(phone)

        # Try database first
        from src.infrastructure.persistence.sqlalchemy.session import get_async_session
        from src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl import UserRepositoryImpl

        user = None
        all_roles: list[str] = []
        try:
            async with get_async_session() as session:
                repo = UserRepositoryImpl(session)
                user = await repo.find_by_phone_number(phone)
                if user is not None:
                    # Fetch all roles — find_by_phone_number already eager-loads via selectin
                    from sqlalchemy import select as sa_select
                    from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
                    result = await session.execute(
                        sa_select(UserModel).where(UserModel.phone == phone)
                    )
                    model = result.scalar_one_or_none()
                    if model and model.roles:
                        all_roles = [r.role for r in model.roles]
        except Exception:
            pass  # DB not available, fall back to env credentials

        if user is not None:
            if not bcrypt.checkpw(pin.encode(), user.pin_hash.encode()):
                self._record_failure(phone)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
            self._record_success(phone)
            # Include ALL roles in JWT — frontend picks highest-privilege for routing
            jwt_roles = all_roles if all_roles else [user.role.value]
            access_token = self._jwt_handler.issue_access_token(
                subject=str(user.user_id),
                claims={
                    "phone": phone,
                    "phone_verified": True,
                    "roles": jwt_roles,
                    "user_id": str(user.user_id),
                },
            )
            return AuthTokenResponse(access_token=access_token, subject=str(user.user_id))

        # Fallback: env-based test credentials (H1: only in dev/test)
        env = os.getenv("TARLA_ENVIRONMENT", os.getenv("APP_ENV", "development"))
        if env in ("development", "test"):
            _test_phone = os.getenv("AUTH_TEST_PHONE")
            _test_pin = os.getenv("AUTH_TEST_PIN")
            if _test_phone and _test_pin:
                if phone == _test_phone and pin == _test_pin:
                    self._record_success(phone)
                    access_token = self._jwt_handler.issue_access_token(
                        subject="user-1",
                        claims={
                            "phone": phone,
                            "phone_verified": True,
                            "roles": ["CENTRAL_ADMIN"],
                            "user_id": "user-1",
                        },
                    )
                    return AuthTokenResponse(access_token=access_token, subject="user-1")

        # No match — record failure
        self._record_failure(phone)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

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
async def phone_pin_login(
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
        result = await service.login(phone=payload.phone, pin=payload.pin)
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


class PhonePinRegisterRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    pin: str = Field(min_length=6, max_length=6)
    province: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=100)
    role: str | None = Field(default=None, max_length=32, description="Optional role code. Defaults to FARMER_SINGLE.")
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)

    @field_validator("pin")
    @classmethod
    def pin_must_be_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must be digits only")
        return v


# Roles that unauthenticated callers may self-register with
_SELF_REGISTER_ROLES = {"FARMER_SINGLE", "FARMER_MEMBER"}


@router.post("/phone-pin/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def phone_pin_register(payload: PhonePinRegisterRequest, request: Request) -> AuthTokenResponse:
    """Register a new user with phone+PIN (KR-050).

    Role selection rules:
    - No auth (self-registration): only FARMER_SINGLE, FARMER_MEMBER allowed.
    - CENTRAL_ADMIN caller: any role from KR-063 allowed.
    """
    import uuid as _uuid
    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.user_repository_impl import UserRepositoryImpl
    from src.core.domain.entities.user import User, UserRole
    from datetime import datetime, timezone

    # Determine target role
    target_role = UserRole.FARMER_SINGLE
    if payload.role is not None:
        try:
            target_role = UserRole(payload.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {payload.role}. Valid roles: {[r.value for r in UserRole]}",
            )

        # Check caller permissions for role assignment
        caller_user = getattr(request.state, "user", None)
        caller_roles = set(getattr(request.state, "roles", []))
        is_admin = "admin" in caller_roles or "CENTRAL_ADMIN" in caller_roles

        if is_admin:
            pass  # Admin can assign any role
        elif target_role.value not in _SELF_REGISTER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only CENTRAL_ADMIN can register users with role {target_role.value}. "
                f"Self-registration allows: {sorted(_SELF_REGISTER_ROLES)}",
            )

    async with get_async_session() as session:
        repo = UserRepositoryImpl(session)
        existing = await repo.find_by_phone_number(payload.phone)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

        now = datetime.now(timezone.utc)
        user = User(
            user_id=_uuid.uuid4(),
            phone_number=payload.phone,
            pin_hash=bcrypt.hashpw(payload.pin.encode(), bcrypt.gensalt()).decode(),
            role=target_role,
            province=payload.province,
            created_at=now,
            updated_at=now,
        )
        await repo.save(user)
        await session.commit()

    jwt_handler = _get_jwt_handler()
    access_token = jwt_handler.issue_access_token(
        subject=str(user.user_id),
        claims={
            "phone": payload.phone,
            "phone_verified": True,
            "roles": [target_role.value],
            "user_id": str(user.user_id),
        },
    )
    return AuthTokenResponse(access_token=access_token, subject=str(user.user_id))


@router.get("/me")
def me(request: Request) -> dict[str, str | bool]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return {
        "subject": str(getattr(user, "subject", "")),
        "phone_verified": bool(getattr(user, "phone_verified", False)),
    }
