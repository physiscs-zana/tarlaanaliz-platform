# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Admin dashboard and analytics aggregate endpoints.
"""Admin dashboard and analytics endpoints — DB aggregate queries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

from typing import Any

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/dashboard")
async def get_dashboard(request: Request) -> dict[str, Any]:
    """Admin dashboard summary — field/mission/analysis/payment counts."""
    _require_admin(request)

    async with get_async_session() as session:
        total_fields = (await session.execute(select(func.count()).select_from(FieldModel))).scalar() or 0

        # Active missions (status = ASSIGNED or IN_PROGRESS)
        active_missions = 0
        try:
            from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel

            active_missions = (
                await session.execute(
                    select(func.count())
                    .select_from(MissionModel)
                    .where(MissionModel.status.in_(["ASSIGNED", "IN_PROGRESS", "PLANNED"]))
                )
            ).scalar() or 0
        except Exception:
            pass  # Mission model may not exist yet

        # Pending payments
        pending_payments = (
            await session.execute(
                select(func.count())
                .select_from(PaymentIntentModel)
                .where(PaymentIntentModel.status.in_(["PAYMENT_PENDING", "PENDING_ADMIN_REVIEW"]))
            )
        ).scalar() or 0

        # Completed analyses (paid intents as proxy)
        completed_analyses = (
            await session.execute(
                select(func.count()).select_from(PaymentIntentModel).where(PaymentIntentModel.status == "PAID")
            )
        ).scalar() or 0

    return {
        "summary": {
            "total_fields": total_fields,
            "active_missions": active_missions,
            "completed_analyses": completed_analyses,
            "pending_payments": pending_payments,
        },
        "recent_activities": [],
    }


@router.get("/analytics")
async def get_analytics(request: Request) -> dict[str, Any]:
    """Admin analytics metrics — expert/review/SLA counts."""
    _require_admin(request)

    async with get_async_session() as session:
        # Total analyses (all payment intents as proxy)
        total_analyses = (await session.execute(select(func.count()).select_from(PaymentIntentModel))).scalar() or 0

        # Active experts (users with EXPERT role)
        active_experts = (
            await session.execute(
                select(func.count(func.distinct(UserRoleModel.user_id))).where(UserRoleModel.role == "EXPERT")
            )
        ).scalar() or 0

        # Pending reviews (PENDING_ADMIN_REVIEW payments)
        pending_reviews = (
            await session.execute(
                select(func.count())
                .select_from(PaymentIntentModel)
                .where(PaymentIntentModel.status == "PENDING_ADMIN_REVIEW")
            )
        ).scalar() or 0

    return {
        "total_analyses": total_analyses,
        "active_experts": active_experts,
        "pending_reviews": pending_reviews,
        "sla_compliance": None,
    }


@router.get("/sla")
async def get_sla_metrics(request: Request) -> dict[str, Any]:
    """Admin SLA summary metrics."""
    _require_admin(request)

    return {
        "review_start_sla_hours": 24,
        "decision_sla_hours": 48,
        "compliance_rate": None,
    }


__all__ = ["router"]
