# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""PostgreSQL Full-Text Search (FTS) indeksleri.

KR-041 (SDLC gates) tam metin arama indeksleri.

Amaç: Kullanıcı adı, tarla konumu gibi alanlar için GIN indeksleri eklemek.
Sorumluluk: Metin arama yeteneklerini PostgreSQL tsvector/GIN ile sağlamak.
Bağımlılıklar: 012 (indexes_performance) migration'ının tamamlanmış olması.
Notlar: PostgreSQL'e özgü; 'turkish' text search config kullanılır.
    Turkish config yoksa 'simple' config fallback olarak kullanılır.

Revision ID: 013
Revises: 012
Create Date: 2026-01-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # pg_trgm extension — trigram tabanlı benzerlik araması için
    # -------------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # -------------------------------------------------------------------------
    # fields tablosu — konum bazlı metin araması
    # -------------------------------------------------------------------------
    # İl + İlçe + Köy/Mahalle birleşik GIN indeksi (trigram)
    op.execute(
        """
        CREATE INDEX idx_fields_location_trgm
        ON fields
        USING GIN ((province || ' ' || district || ' ' || COALESCE(village, '')) gin_trgm_ops)
        """
    )

    # Ada/Parsel referansı trigram indeksi (block_no + parcel_no birleşik)
    op.execute(
        """
        CREATE INDEX idx_fields_parcel_ref_trgm
        ON fields
        USING GIN ((block_no || ' ' || parcel_no) gin_trgm_ops)
        """
    )

    # Bitki türü GIN indeksi
    op.execute(
        """
        CREATE INDEX idx_fields_crop_type_trgm
        ON fields
        USING GIN (crop_type gin_trgm_ops)
        """
    )

    # -------------------------------------------------------------------------
    # users tablosu — kullanıcı araması
    # -------------------------------------------------------------------------
    # Telefon numarası prefix araması (B-Tree yeterli, ama trigram daha esnek)
    op.execute(
        """
        CREATE INDEX idx_users_phone_trgm
        ON users
        USING GIN (phone gin_trgm_ops)
        """
    )

    # -------------------------------------------------------------------------
    # pilots tablosu — pilot araması
    # -------------------------------------------------------------------------
    # Not: pilots tablosunda full_name sütunu yok; ad bilgisi users tablosunda
    # tutulur. Pilot araması için konum indeksi yeterlidir.

    # Pilot ili + ilçe birleşik trigram indeksi
    op.execute(
        """
        CREATE INDEX idx_pilots_location_trgm
        ON pilots
        USING GIN ((province || ' ' || COALESCE(district, '')) gin_trgm_ops)
        """
    )

    # -------------------------------------------------------------------------
    # audit_logs tablosu — event_type ve error_message araması
    # -------------------------------------------------------------------------
    op.execute(
        """
        CREATE INDEX idx_audit_logs_error_trgm
        ON audit_logs
        USING GIN (error_message gin_trgm_ops)
        WHERE error_message IS NOT NULL
        """
    )


def downgrade() -> None:
    # audit_logs
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_error_trgm")

    # pilots
    op.execute("DROP INDEX IF EXISTS idx_pilots_location_trgm")

    # users
    op.execute("DROP INDEX IF EXISTS idx_users_phone_trgm")

    # fields
    op.execute("DROP INDEX IF EXISTS idx_fields_crop_type_trgm")
    op.execute("DROP INDEX IF EXISTS idx_fields_parcel_ref_trgm")
    op.execute("DROP INDEX IF EXISTS idx_fields_location_trgm")

    # Extension — dikkatli olun: diğer migration'lar kullanıyor olabilir
    # Güvenli olmak için extension'ı kaldırmıyoruz
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm")
