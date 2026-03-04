# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Infrastructure layer — adapter/implementation package.
"""Infrastructure layer public API.

Alt paketler:
  - config: Uygulama yapılandırması (Settings).
  - external: Dış servis adapter'ları (S3, SMS, Payment, AV Scanner, vb.).
  - integrations: Provider-spesifik entegrasyonlar (Cloudflare, NetGSM, Twilio, vb.).
  - messaging: Event bus ve kuyruk implementasyonları (RabbitMQ, WebSocket).
  - monitoring: Sağlık kontrolü, metrikler, güvenlik olay kaydı.
  - notifications: Bildirim servisleri.
  - persistence: Veritabanı (SQLAlchemy) ve önbellek (Redis) implementasyonları.
  - security: Şifreleme, JWT, rate limit, sorgu güvenliği.
  - contracts: Schema registry.
"""

from . import (
    config,
    contracts,
    external,
    integrations,
    messaging,
    monitoring,
    notifications,
    persistence,
    security,
)

__all__: list[str] = [
    "config",
    "contracts",
    "external",
    "integrations",
    "messaging",
    "monitoring",
    "notifications",
    "persistence",
    "security",
]
