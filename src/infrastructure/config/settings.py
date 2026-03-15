# PATH: src/infrastructure/config/settings.py
# DESC: Platform konfigürasyonunu ENV'den yüklemek.
"""
Platform konfigürasyonu: tüm dış bağımlılık parametrelerini ENV'den yükler.

pydantic-settings ile tip-güvenli konfigürasyon. Her ayar ENV değişkeninden
okunur; .env dosyası opsiyonel olarak desteklenir.

SSOT: tarlaanaliz_platform_tree v3.2.2 FINAL.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform konfigürasyon ayarları.

    Tüm ayarlar ENV'den okunur. Prefix: TARLA_
    .env dosyası mevcut ise otomatik yüklenir.
    """

    model_config = SettingsConfigDict(
        env_prefix="TARLA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    app_name: str = "tarlaanaliz-platform"
    app_version: str = "3.2.2"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # ------------------------------------------------------------------
    # API / Uvicorn
    # ------------------------------------------------------------------
    api_host: str = "0.0.0.0"  # noqa: S104
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: str = ""
    api_prefix: str = "/api/v1"

    # ------------------------------------------------------------------
    # PostgreSQL (asyncpg)
    # ------------------------------------------------------------------
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "tarlaanaliz"
    db_user: str = "tarlaanaliz"
    db_password: SecretStr = SecretStr("")
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy bağlantı URL'i (asyncpg)."""
        password = self.db_password.get_secret_value()
        return f"postgresql+asyncpg://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        """Sync SQLAlchemy bağlantı URL'i (Alembic migration'ları için)."""
        password = self.db_password.get_secret_value()
        return f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr = SecretStr("")

    @property
    def redis_url(self) -> str:
        """Redis bağlantı URL'i."""
        password = self.redis_password.get_secret_value()
        if password:
            return f"redis://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ------------------------------------------------------------------
    # RabbitMQ (aio-pika)
    # ------------------------------------------------------------------
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "tarlaanaliz"
    rabbitmq_password: SecretStr = SecretStr("")
    rabbitmq_vhost: str = "/"

    @property
    def rabbitmq_url(self) -> str:
        """AMQP bağlantı URL'i."""
        password = self.rabbitmq_password.get_secret_value()
        return f"amqp://{self.rabbitmq_user}:{password}@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"

    # ------------------------------------------------------------------
    # JWT / Auth
    # ------------------------------------------------------------------
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_algorithm: str = "HS256"

    @property
    def jwt_secret_key_value(self) -> str:
        """Fail-fast if JWT secret is empty or default."""
        val = self.jwt_secret_key.get_secret_value()
        if not val or val == "CHANGE-ME-IN-PRODUCTION":
            raise ValueError(
                "TARLA_JWT_SECRET_KEY must be set to a strong random value. "
                "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return val
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ------------------------------------------------------------------
    # Object Storage (S3 / MinIO)
    # ------------------------------------------------------------------
    s3_endpoint_url: str = ""
    s3_access_key_id: SecretStr = SecretStr("")
    s3_secret_access_key: SecretStr = SecretStr("")
    s3_region: str = "eu-west-1"
    s3_default_bucket: str = "tarlaanaliz-data"
    s3_presigned_url_expire_seconds: int = 3600

    # ------------------------------------------------------------------
    # Payment Gateway
    # ------------------------------------------------------------------
    payment_provider: str = "iyzico"
    payment_api_url: str = ""
    payment_api_key: SecretStr = SecretStr("")
    payment_secret_key: SecretStr = SecretStr("")
    payment_timeout_seconds: int = 30

    # ------------------------------------------------------------------
    # SMS Gateway
    # ------------------------------------------------------------------
    sms_provider: str = "netgsm"
    sms_api_url: str = ""
    sms_api_key: SecretStr = SecretStr("")
    sms_sender_id: str = "TARLAANLZ"
    sms_timeout_seconds: int = 15

    # ------------------------------------------------------------------
    # TKGM / MEGSİS WFS
    # ------------------------------------------------------------------
    tkgm_wfs_base_url: str = ""
    tkgm_wfs_timeout_seconds: int = 30
    tkgm_cache_ttl_seconds: int = 86400  # 24 saat

    # ------------------------------------------------------------------
    # Weather API
    # ------------------------------------------------------------------
    weather_api_url: str = ""
    weather_api_key: SecretStr = SecretStr("")
    weather_timeout_seconds: int = 15

    # ------------------------------------------------------------------
    # AI Worker / Feedback Pipeline
    # ------------------------------------------------------------------
    ai_worker_api_url: str = ""
    ai_worker_api_key: SecretStr = SecretStr("")
    ai_worker_timeout_seconds: int = 60

    # ------------------------------------------------------------------
    # Cloudflare (DDoS Protection)
    # ------------------------------------------------------------------
    cloudflare_api_url: str = "https://api.cloudflare.com/client/v4"
    cloudflare_api_token: SecretStr = SecretStr("")
    cloudflare_zone_id: str = ""
    cloudflare_timeout_seconds: int = 15

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------
    sentry_dsn: str = ""
    prometheus_enabled: bool = True

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------
    rate_limit_requests_per_minute: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton Settings instance döner (LRU cache ile)."""
    return Settings()
