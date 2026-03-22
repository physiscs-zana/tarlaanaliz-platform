# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: API middleware configuration; JWT, CORS, rate-limit, anomaly settings.
"""API settings for middleware and app wiring."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _require_env(name: str, fallback: str = "") -> str:
    """Return env var value, fallback, or raise if both missing — used for secrets."""
    value = os.getenv(name)
    if value:
        return value
    if fallback:
        return fallback
    raise ValueError(f"{name} environment variable is required")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_list(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
    return parsed or default


def _docs_url(name: str, default: str) -> str | None:
    """Return docs URL or None when explicitly disabled or in production."""
    env = os.getenv("TARLA_ENVIRONMENT", os.getenv("APP_ENV", "development"))
    explicit = os.getenv(name)
    if explicit is not None:
        return None if explicit.strip().lower() in {"", "none", "false", "off"} else explicit
    # Disable docs in production by default — set API_DOCS_URL=/docs to override
    if env == "production":
        return None
    return default


@dataclass(slots=True)
class AppSettings:
    title: str = field(default_factory=lambda: os.getenv("API_TITLE", "TarlaAnaliz Platform API"))
    version: str = field(default_factory=lambda: os.getenv("API_VERSION", "1.0.0"))
    docs_url: str | None = field(default_factory=lambda: _docs_url("API_DOCS_URL", "/docs"))
    redoc_url: str | None = field(default_factory=lambda: _docs_url("API_REDOC_URL", "/redoc"))
    openapi_url: str | None = field(default_factory=lambda: _docs_url("API_OPENAPI_URL", "/openapi.json"))


@dataclass(slots=True)
class CorsSettings:
    enabled: bool = field(default_factory=lambda: _env_bool("API_CORS_ENABLED", True))
    # SEC-FIX: Boş default yerine production whitelist — CORS misconfiguration önlenir
    allow_origins: list[str] = field(
        default_factory=lambda: _env_list(
            "API_CORS_ALLOW_ORIGINS",
            ["https://tarlaanaliz.com", "https://www.tarlaanaliz.com"],
        )
    )
    allow_methods: list[str] = field(
        default_factory=lambda: _env_list(
            "API_CORS_ALLOW_METHODS", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        )
    )
    allow_headers: list[str] = field(
        default_factory=lambda: _env_list(
            "API_CORS_ALLOW_HEADERS", ["Authorization", "Content-Type", "X-Correlation-Id"]
        )
    )
    allow_credentials: bool = field(default_factory=lambda: _env_bool("API_CORS_ALLOW_CREDENTIALS", False))


_JWT_INSECURE_FALLBACK = "test-only-insecure-key-do-not-use-in-prod"


@dataclass(slots=True)
class JwtSettings:
    enabled: bool = field(default_factory=lambda: _env_bool("API_JWT_ENABLED", True))
    bypass_routes: list[str] = field(
        default_factory=lambda: _env_list(
            "API_JWT_BYPASS_ROUTES",
            [
                "/health",
                "/docs",
                "/openapi.json",
                "/redoc",
                "/api/v1/auth/phone-pin/login",
                "/api/v1/auth/phone-pin/register",
                "/api/v1/auth/phone-pin/refresh",
                "/api/v1/auth/logout",
                "/api/v1/payments/webhooks/provider",
                "/api/v1/payments/methods",
            ],
        )
    )
    secret: str = field(default_factory=lambda: _require_env("API_JWT_SECRET", _JWT_INSECURE_FALLBACK))
    algorithm: str = field(default_factory=lambda: os.getenv("API_JWT_ALGORITHM", "HS256"))

    def __post_init__(self) -> None:
        env = os.getenv("TARLA_ENVIRONMENT", os.getenv("APP_ENV", "development"))
        if env == "production" and self.secret == _JWT_INSECURE_FALLBACK:
            raise ValueError(
                "CRITICAL: JWT secret must be configured in production! "
                "Set API_JWT_SECRET environment variable to a strong random key."
            )


@dataclass(slots=True)
class RateLimitSettings:
    enabled: bool = field(default_factory=lambda: _env_bool("API_RATE_LIMIT_ENABLED", True))
    per_minute_limit: int = field(default_factory=lambda: _env_int("API_RATE_LIMIT_PER_MINUTE", 61))
    burst: int = field(default_factory=lambda: _env_int("API_RATE_LIMIT_BURST", 20))
    bypass_routes: list[str] = field(
        default_factory=lambda: _env_list("API_RATE_LIMIT_BYPASS_ROUTES", ["/health", "/docs", "/openapi.json"])
    )


@dataclass(slots=True)
class AnomalySettings:
    enabled: bool = field(default_factory=lambda: _env_bool("API_ANOMALY_ENABLED", True))
    allowlist_routes: list[str] = field(
        default_factory=lambda: _env_list("API_ANOMALY_ALLOWLIST_ROUTES", ["/health", "/docs", "/openapi.json"])
    )
    rapid_repeat_window_seconds: int = field(default_factory=lambda: _env_int("API_ANOMALY_REPEAT_WINDOW_SECONDS", 10))
    rapid_repeat_threshold: int = field(default_factory=lambda: _env_int("API_ANOMALY_REPEAT_THRESHOLD", 8))
    large_body_threshold_bytes: int = field(default_factory=lambda: _env_int("API_ANOMALY_LARGE_BODY_BYTES", 1_000_000))


@dataclass(slots=True)
class ApiSettings:
    app: AppSettings = field(default_factory=AppSettings)
    cors: CorsSettings = field(default_factory=CorsSettings)
    jwt: JwtSettings = field(default_factory=JwtSettings)
    rate_limit: RateLimitSettings = field(default_factory=RateLimitSettings)
    anomaly: AnomalySettings = field(default_factory=AnomalySettings)


settings = ApiSettings()
