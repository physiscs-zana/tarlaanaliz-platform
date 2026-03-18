# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# SEC: OTP service infrastructure — prepared but NOT ACTIVE until SMS provider is configured.
"""OTP (One-Time Password) service for phone verification.

This module provides the infrastructure for SMS-based OTP verification.
Currently prepared but NOT ACTIVE — activation requires:
1. SMS provider configuration (e.g. Twilio, Netgsm)
2. Setting OTP_ENABLED=true in environment
3. Uncommenting the OTP endpoints in auth.py

Flow:
  1. POST /auth/phone-pin/request-otp  -> Generate & send 6-digit OTP via SMS
  2. POST /auth/phone-pin/verify-otp   -> Verify OTP, return registration_token
  3. POST /auth/phone-pin/register     -> registration_token + phone + pin
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import time

LOGGER = logging.getLogger("security.otp")

_OTP_LENGTH = 6
_OTP_TTL_SECONDS = 300  # 5 minutes
_OTP_MAX_ATTEMPTS = 3
_OTP_DAILY_LIMIT = 5  # Max OTP requests per phone per day
_OTP_PREFIX = "otp:"
_OTP_DAILY_PREFIX = "otp_daily:"
_REG_TOKEN_PREFIX = "reg_token:"
_REG_TOKEN_TTL = 600  # 10 minutes


def _generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return "".join(str(secrets.randbelow(10)) for _ in range(_OTP_LENGTH))


def _hash_otp(otp: str, phone: str) -> str:
    """Hash OTP with phone as salt for secure storage."""
    return hashlib.sha256(f"{phone}:{otp}".encode()).hexdigest()


async def request_otp(phone: str) -> dict[str, str]:
    """Generate OTP and store in Redis. Returns status message.

    Rate limits:
    - Max 5 OTP requests per phone per day
    - OTP valid for 5 minutes
    - Max 3 verification attempts per OTP
    """
    from src.infrastructure.persistence.redis.cache import get_redis_client
    client = await get_redis_client()

    # Check daily limit
    daily_key = f"{_OTP_DAILY_PREFIX}{phone}:{int(time.time()) // 86400}"
    daily_count = await client.get(daily_key)
    if daily_count and int(daily_count) >= _OTP_DAILY_LIMIT:
        return {"status": "error", "message": "Gunluk OTP limiti asildi. Yarin tekrar deneyin."}

    # Generate OTP
    otp = _generate_otp()
    otp_hash = _hash_otp(otp, phone)

    # Store in Redis
    otp_key = f"{_OTP_PREFIX}{phone}"
    await client.hset(otp_key, mapping={
        "otp_hash": otp_hash,
        "attempts": "0",
        "created_at": str(time.time()),
    })
    await client.expire(otp_key, _OTP_TTL_SECONDS)

    # Increment daily counter
    await client.incr(daily_key)
    await client.expire(daily_key, 86400)

    # Send SMS (placeholder — requires SMS provider)
    sms_provider = os.getenv("SMS_PROVIDER", "")
    if sms_provider:
        await _send_sms(phone, otp, sms_provider)
        LOGGER.info("otp_sent", extra={"phone_tail": phone[-4:], "provider": sms_provider})
    else:
        LOGGER.warning("otp_generated_but_no_sms_provider", extra={"phone_tail": phone[-4:]})
        # In development, log the OTP for testing
        env = os.getenv("TARLA_ENVIRONMENT", os.getenv("APP_ENV", "development"))
        if env in ("development", "test"):
            LOGGER.info("dev_otp_code", extra={"phone_tail": phone[-4:], "otp": otp})

    return {"status": "ok", "message": "Dogrulama kodu gonderildi."}


async def verify_otp(phone: str, otp: str) -> dict[str, str]:
    """Verify OTP and return a registration token if valid."""
    from src.infrastructure.persistence.redis.cache import get_redis_client
    client = await get_redis_client()

    otp_key = f"{_OTP_PREFIX}{phone}"
    record = await client.hgetall(otp_key)

    if not record:
        return {"status": "error", "message": "Dogrulama kodu bulunamadi veya suresi doldu."}

    attempts = int(record.get("attempts", "0"))
    if attempts >= _OTP_MAX_ATTEMPTS:
        await client.delete(otp_key)
        return {"status": "error", "message": "Cok fazla hatali deneme. Yeni kod isteyin."}

    # Increment attempts
    await client.hincrby(otp_key, "attempts", 1)

    # Verify
    otp_hash = _hash_otp(otp, phone)
    if otp_hash != record.get("otp_hash"):
        remaining = _OTP_MAX_ATTEMPTS - attempts - 1
        return {"status": "error", "message": f"Hatali kod. {remaining} deneme hakkiniz kaldi."}

    # OTP valid — clean up and issue registration token
    await client.delete(otp_key)

    # Generate registration token
    reg_token = secrets.token_urlsafe(32)
    reg_key = f"{_REG_TOKEN_PREFIX}{reg_token}"
    await client.setex(reg_key, _REG_TOKEN_TTL, phone)

    LOGGER.info("otp_verified", extra={"phone_tail": phone[-4:]})
    return {"status": "ok", "registration_token": reg_token}


async def validate_registration_token(token: str) -> str | None:
    """Validate registration token and return the associated phone number."""
    from src.infrastructure.persistence.redis.cache import get_redis_client
    client = await get_redis_client()

    reg_key = f"{_REG_TOKEN_PREFIX}{token}"
    phone = await client.get(reg_key)
    if phone:
        await client.delete(reg_key)  # One-time use
    return phone


async def _send_sms(phone: str, otp: str, provider: str) -> None:
    """Send SMS via configured provider. Placeholder for real implementation."""
    # TODO: Implement actual SMS sending when provider is chosen
    # Supported providers: netgsm, twilio, vonage
    LOGGER.info("sms_send_placeholder", extra={
        "phone_tail": phone[-4:],
        "provider": provider,
        "message": f"TarlaAnaliz dogrulama kodunuz: {otp}",
    })
