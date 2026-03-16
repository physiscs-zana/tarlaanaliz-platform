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
from sqlalchemy import engine_from_config, pool, text as sa_text

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
    """Veritabani URL'sini ortam degiskeninden al.

    Oncelik sirasi:
    1. DATABASE_URL ortam degiskeni
    2. TARLA_ prefix'li ayri env var'lardan olustur
    3. alembic.ini'deki sqlalchemy.url
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    # TARLA_ prefix'li env var'lardan URL olustur (docker-compose uyumu)
    host = os.environ.get("TARLA_DB_HOST") or os.environ.get("DB_HOST")
    port = os.environ.get("TARLA_DB_PORT") or os.environ.get("DB_PORT")
    user = os.environ.get("TARLA_DB_USER") or os.environ.get("DB_USER")
    password = os.environ.get("TARLA_DB_PASSWORD") or os.environ.get("DB_PASSWORD")
    name = os.environ.get("TARLA_DB_NAME") or os.environ.get("DB_NAME")
    if host and user and name:
        pwd = f":{password}" if password else ""
        p = f":{port}" if port else ""
        return f"postgresql://{user}{pwd}@{host}{p}/{name}"

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
