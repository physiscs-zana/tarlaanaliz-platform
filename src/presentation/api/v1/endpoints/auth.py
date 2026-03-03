# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# KR-050: Telefon + 6 haneli PIN (sabit uzunluk, yalnızca rakam).
# KR-081: contract-first auth; no email/TCKN/OTP.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/auth", tags=["auth"])

# KR-050: Sabit 6 haneli sayısal PIN (v1.1.0 — eski: 4-12 chars)
_PIN_LENGTH = 6
_MAX_FAILED_LOGIN_ATTEMPTS = 16   # KR-050: 16 hata → 30 dakika kilit


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
    def login(self, phone: str, pin: str) -> AuthTokenResponse:
        ...

    def refresh(self, refresh_token: str) -> AuthTokenResponse:
        ...


@dataclass(slots=True)
class _InMemoryPhonePinAuthService:
    def login(self, phone: str, pin: str) -> AuthTokenResponse:
        # KR-081: explicit auth contract; no email/TCKN/OTP fields accepted.
        if phone != "+905555555555" or pin != "1234":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        return AuthTokenResponse(access_token="demo-access-token", subject="user-1")

    def refresh(self, refresh_token: str) -> AuthTokenResponse:
        if refresh_token != "demo-refresh-token":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        return AuthTokenResponse(access_token="demo-access-token-refreshed", subject="user-1")


def get_phone_pin_auth_service() -> PhonePinAuthService:
    return _InMemoryPhonePinAuthService()


@router.post("/phone-pin/login", response_model=AuthTokenResponse)
def phone_pin_login(payload: PhonePinLoginRequest, service: PhonePinAuthService = Depends(get_phone_pin_auth_service)) -> AuthTokenResponse:
    return service.login(phone=payload.phone, pin=payload.pin)


@router.post("/phone-pin/refresh", response_model=AuthTokenResponse)
def phone_pin_refresh(payload: AuthRefreshRequest, service: PhonePinAuthService = Depends(get_phone_pin_auth_service)) -> AuthTokenResponse:
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
