# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Expert reviews and feedback records schema.

KR-019 ve KR-029 (Feedback Loop) geregi expert_reviews ve
feedback_records tablolarini olusturmak.

Revision ID: 008
Revises: 007
Create Date: 2026-01-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Review status enum --
    review_status_enum = postgresql.ENUM(
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "ESCALATED",
        "EXPIRED",
        name="review_status",
        create_type=True,
    )
    review_status_enum.create(op.get_bind(), checkfirst=True)

    # -- Verdict enum (KR-019) --
    verdict_enum = postgresql.ENUM(
        "confirmed",
        "corrected",
        "rejected",
        "needs_more_expert",
        name="expert_verdict",
        create_type=True,
    )
    verdict_enum.create(op.get_bind(), checkfirst=True)

    # -- Training grade enum (KR-019/KR-029) --
    training_grade_enum = postgresql.ENUM(
        "A",
        "B",
        "C",
        "D",
        "REJECT",
        name="training_grade",
        create_type=True,
    )
    training_grade_enum.create(op.get_bind(), checkfirst=True)

    # -- Expert reviews tablosu (KR-019: uzman inceleme) --
    op.create_table(
        "expert_reviews",
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_results.result_id"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=False,
        ),
        sa.Column(
            "expert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experts.expert_id"),
            nullable=True,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "IN_PROGRESS",
                "COMPLETED",
                "ESCALATED",
                "EXPIRED",
                name="review_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "verdict",
            postgresql.ENUM(
                "confirmed",
                "corrected",
                "rejected",
                "needs_more_expert",
                name="expert_verdict",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("corrected_class", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        # Trigger confidence threshold
        sa.Column("trigger_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # SLA: 4 saat icinde yanitlanmali (SC-EXP-05)
        sa.Column("sla_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_to_expert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experts.expert_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_expert_reviews_expert", "expert_reviews", ["expert_id", "status"])
    op.create_index("ix_expert_reviews_result", "expert_reviews", ["result_id"])
    op.create_index("ix_expert_reviews_mission", "expert_reviews", ["mission_id"])
    op.create_index("ix_expert_reviews_sla", "expert_reviews", ["status", "sla_deadline_at"])

    # -- Feedback records tablosu (KR-029 kanonik SQL'den) --
    op.create_table(
        "feedback_records",
        sa.Column(
            "feedback_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expert_reviews.review_id"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=False,
        ),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column(
            "verdict",
            postgresql.ENUM(
                "confirmed",
                "corrected",
                "rejected",
                "needs_more_expert",
                name="expert_verdict",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("corrected_class", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "training_grade",
            postgresql.ENUM("A", "B", "C", "D", "REJECT", name="training_grade", create_type=False),
            nullable=False,
        ),
        sa.Column("grade_reason", sa.String(200), nullable=True),
        sa.Column("expert_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("image_quality", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("no_conflict", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_feedback_grade", "feedback_records", ["training_grade", sa.text("created_at DESC")])
    op.create_index("ix_feedback_mission_created", "feedback_records", ["mission_id", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("feedback_records")
    op.drop_table("expert_reviews")

    op.execute("DROP TYPE IF EXISTS training_grade")
    op.execute("DROP TYPE IF EXISTS expert_verdict")
    op.execute("DROP TYPE IF EXISTS review_status")
