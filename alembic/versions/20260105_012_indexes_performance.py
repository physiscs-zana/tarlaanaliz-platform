# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Veritabanı performans optimizasyonu için B-Tree indeksleri.

KR-041 (SDLC gates) performans indeksleri — sorgu optimizasyonu.

Amaç: Sık sorgulanan alanlara (status, due_at, user_id, field_id) B-Tree indeksleri eklemek.
Sorumluluk: Sorgu performansını artırmak için composite ve tek sütun indekslerini oluşturmak.
Bağımlılıklar: 001-011 arası tüm tablo migration'larının tamamlanmış olması gerekir.

Revision ID: 012
Revises: 011
Create Date: 2026-01-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # missions tablosu indeksleri
    # -------------------------------------------------------------------------
    # Durum + son tarih bazlı sorgular (planlama, SLA takibi)
    op.create_index(
        "idx_missions_status_due",
        "missions",
        ["status", "due_at"],
        unique=False,
    )
    # Tarla bazlı mission geçmişi (en yeni önce)
    op.create_index(
        "idx_missions_field_created",
        "missions",
        ["field_id", sa.text("created_at DESC")],
        unique=False,
    )
    # Abonelik bazlı mission listesi
    op.create_index(
        "idx_missions_subscription",
        "missions",
        ["subscription_id", sa.text("created_at DESC")],
        unique=False,
    )
    # Ödeme referansı ile mission arama
    op.create_index(
        "idx_missions_payment_intent",
        "missions",
        ["payment_intent_id"],
        unique=False,
    )
    # Pilot ataması bazlı sorgular
    op.create_index(
        "idx_missions_pilot_status",
        "missions",
        ["pilot_id", "status"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # subscriptions tablosu indeksleri
    # -------------------------------------------------------------------------
    # Zamanlayıcı sorgusu: aktif aboneliklerin due tarihine göre taranması
    op.create_index(
        "idx_subscriptions_due",
        "subscriptions",
        ["status", "next_due_at"],
        unique=False,
    )
    # Tarla bazlı abonelik durumu
    op.create_index(
        "idx_subscriptions_field",
        "subscriptions",
        ["field_id", "status"],
        unique=False,
    )
    # Ödeme referansı ile abonelik arama
    op.create_index(
        "idx_subscriptions_payment_intent",
        "subscriptions",
        ["payment_intent_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # payment_intents tablosu indeksleri
    # -------------------------------------------------------------------------
    # Hedef (mission/subscription) bazlı ödeme arama
    op.create_index(
        "idx_payment_intents_target",
        "payment_intents",
        ["target_type", "target_id"],
        unique=False,
    )
    # Durum bazlı ödeme listesi (en yeni önce)
    op.create_index(
        "idx_payment_intents_status",
        "payment_intents",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )
    # Ödeme yapan kullanıcı bazlı arama
    op.create_index(
        "idx_payment_intents_payer",
        "payment_intents",
        ["payer_user_id", sa.text("created_at DESC")],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # analysis_jobs tablosu indeksleri
    # -------------------------------------------------------------------------
    # Mission bazlı analiz işi arama
    op.create_index(
        "idx_analysis_jobs_mission",
        "analysis_jobs",
        ["mission_id"],
        unique=False,
    )
    # Durum bazlı analiz kuyruğu
    op.create_index(
        "idx_analysis_jobs_status",
        "analysis_jobs",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # analysis_results tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_analysis_results_mission",
        "analysis_results",
        ["mission_id"],
        unique=False,
    )
    op.create_index(
        "idx_analysis_results_job",
        "analysis_results",
        ["job_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # expert_reviews tablosu indeksleri
    # -------------------------------------------------------------------------
    # Uzman bazlı bekleyen incelemeler
    op.create_index(
        "idx_expert_reviews_expert_status",
        "expert_reviews",
        ["expert_id", "status"],
        unique=False,
    )
    # Mission bazlı inceleme arama
    op.create_index(
        "idx_expert_reviews_mission",
        "expert_reviews",
        ["mission_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # audit_logs tablosu indeksleri
    # -------------------------------------------------------------------------
    # Olay türü bazlı log arama
    op.create_index(
        "idx_audit_logs_event_type",
        "audit_logs",
        ["event_type", sa.text("created_at DESC")],
        unique=False,
    )
    # Aktör bazlı log arama
    op.create_index(
        "idx_audit_logs_actor",
        "audit_logs",
        ["actor_id_hash", sa.text("created_at DESC")],
        unique=False,
    )
    # Correlation ID ile istek zinciri takibi
    op.create_index(
        "idx_audit_logs_correlation",
        "audit_logs",
        ["correlation_id"],
        unique=False,
    )
    # Mission bazlı audit trail
    op.create_index(
        "idx_audit_logs_mission",
        "audit_logs",
        ["mission_id", sa.text("created_at DESC")],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # weather_block_reports tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_weather_blocks_mission",
        "weather_block_reports",
        ["mission_id"],
        unique=False,
    )
    op.create_index(
        "idx_weather_blocks_status",
        "weather_block_reports",
        ["status"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # calibration_records tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_calibration_records_mission",
        "calibration_records",
        ["mission_id"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # qc_reports tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_qc_reports_status",
        "qc_reports",
        ["status"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # feedback_records tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_feedback_grade",
        "feedback_records",
        ["training_grade", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_feedback_mission",
        "feedback_records",
        ["mission_id", sa.text("created_at DESC")],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # price_snapshots tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_price_snapshots_crop_type",
        "price_snapshots",
        ["crop_type", "analysis_type", "effective_from"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # fields tablosu indeksleri
    # -------------------------------------------------------------------------
    # Kullanıcı bazlı tarla listesi
    op.create_index(
        "idx_fields_user",
        "fields",
        ["user_id", "status"],
        unique=False,
    )
    # İl/İlçe bazlı tarla arama
    op.create_index(
        "idx_fields_province_district",
        "fields",
        ["province", "district"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # users tablosu indeksleri
    # -------------------------------------------------------------------------
    # Not: users.role sütunu yok; roller user_roles junction tablosunda tutulur.
    # İl bazlı kullanıcı arama
    op.create_index(
        "idx_users_province",
        "users",
        ["province"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # pilots tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_pilots_province_status",
        "pilots",
        ["province", "is_active"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # weekly_schedules tablosu indeksleri
    # -------------------------------------------------------------------------
    # Not: weekly_schedules tablosunda pilot_id sütunu yok; pilot atamaları
    # schedule_entries üzerinden takip edilir. Bu nedenle ayrı indeks eklenmez.

    # -------------------------------------------------------------------------
    # mission_route_files tablosu indeksleri
    # -------------------------------------------------------------------------
    op.create_index(
        "idx_route_files_parcel",
        "mission_route_files",
        ["parcel_ref"],
        unique=False,
    )


def downgrade() -> None:
    # mission_route_files
    op.drop_index("idx_route_files_parcel", table_name="mission_route_files")

    # pilots
    op.drop_index("idx_pilots_province_status", table_name="pilots")

    # users
    op.drop_index("idx_users_province", table_name="users")

    # fields
    op.drop_index("idx_fields_province_district", table_name="fields")
    op.drop_index("idx_fields_user", table_name="fields")

    # price_snapshots
    op.drop_index("idx_price_snapshots_crop_type", table_name="price_snapshots")

    # feedback_records
    op.drop_index("idx_feedback_mission", table_name="feedback_records")
    op.drop_index("idx_feedback_grade", table_name="feedback_records")

    # qc_reports
    op.drop_index("idx_qc_reports_status", table_name="qc_reports")

    # calibration_records
    op.drop_index("idx_calibration_records_mission", table_name="calibration_records")

    # weather_block_reports
    op.drop_index("idx_weather_blocks_status", table_name="weather_block_reports")
    op.drop_index("idx_weather_blocks_mission", table_name="weather_block_reports")

    # audit_logs
    op.drop_index("idx_audit_logs_mission", table_name="audit_logs")
    op.drop_index("idx_audit_logs_correlation", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor", table_name="audit_logs")
    op.drop_index("idx_audit_logs_event_type", table_name="audit_logs")

    # expert_reviews
    op.drop_index("idx_expert_reviews_mission", table_name="expert_reviews")
    op.drop_index("idx_expert_reviews_expert_status", table_name="expert_reviews")

    # analysis_results
    op.drop_index("idx_analysis_results_job", table_name="analysis_results")
    op.drop_index("idx_analysis_results_mission", table_name="analysis_results")

    # analysis_jobs
    op.drop_index("idx_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("idx_analysis_jobs_mission", table_name="analysis_jobs")

    # payment_intents
    op.drop_index("idx_payment_intents_payer", table_name="payment_intents")
    op.drop_index("idx_payment_intents_status", table_name="payment_intents")
    op.drop_index("idx_payment_intents_target", table_name="payment_intents")

    # subscriptions
    op.drop_index("idx_subscriptions_payment_intent", table_name="subscriptions")
    op.drop_index("idx_subscriptions_field", table_name="subscriptions")
    op.drop_index("idx_subscriptions_due", table_name="subscriptions")

    # missions
    op.drop_index("idx_missions_pilot_status", table_name="missions")
    op.drop_index("idx_missions_payment_intent", table_name="missions")
    op.drop_index("idx_missions_subscription", table_name="missions")
    op.drop_index("idx_missions_field_created", table_name="missions")
    op.drop_index("idx_missions_status_due", table_name="missions")
