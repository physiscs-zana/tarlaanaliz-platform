# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SDLC gate — migration runtime environment.
"""
Amaç: Alembic çalışma zamanı ortamı (Runtime Environment).
Sorumluluk: SQLAlchemy modellerini (metadata) yükleyerek veritabanı ile kod arasındaki
    farkı hesaplamak ve migration scriptlerini çalıştırmak.
Girdi/Çıktı (Contract/DTO/Event): Girdi: Alembic komutu. Çıktı: DB şema değişikliği.
Güvenlik (RBAC/PII/Audit): DB credentials env'den okunur.
Hata Modları (idempotency/retry/rate limit): DB bağlantı hatası.
Observability (log fields/metrics/traces): Migration logları.
Testler: N/A
Bağımlılıklar: Alembic, SQLAlchemy.
Notlar/SSOT: Migration motoru.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# src/ dizinini sys.path'e ekle (model importları için)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Alembic Config nesnesi (.ini dosyasına erişim sağlar)
config = context.config

# Python logging konfigürasyonunu .ini'den oku
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# SQLAlchemy metadata — autogenerate desteği için
# ---------------------------------------------------------------------------
# Model importları: tüm modeller Base.metadata'ya kayıtlı olmalıdır.
# Şu an modeller TODO aşamasında; metadata import edildiğinde autogenerate çalışır.
try:
    from src.infrastructure.persistence.sqlalchemy.models.base import Base

    target_metadata = Base.metadata
except ImportError:
    target_metadata = None


def get_url() -> str:
    """Veritabanı URL'sini ortam değişkeninden al.

    Öncelik sırası:
    1. DATABASE_URL ortam değişkeni
    2. alembic.ini'deki sqlalchemy.url
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        # asyncpg URL'lerini senkron sürücüye dönüştür
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url
    return config.get_main_option("sqlalchemy.url", "postgresql://localhost/tarlaanaliz")


def run_migrations_offline() -> None:
    """'Offline' modda migration çalıştır.

    Bu mod gerçek bir DB bağlantısı gerektirmez;
    sadece SQL çıktısı üretir (--sql flag'i ile).
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """'Online' modda migration çalıştır.

    Gerçek bir DB bağlantısı kurulur ve migration'lar transaction içinde çalıştırılır.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
