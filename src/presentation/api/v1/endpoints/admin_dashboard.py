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

    import sqlalchemy as sa

    total_fields = 0
    active_missions = 0
    pending_payments = 0
    completed_analyses = 0
    total_users = 0

    try:
        async with get_async_session() as session:
            total_fields = (await session.execute(select(func.count()).select_from(FieldModel))).scalar() or 0
            total_users = (await session.execute(select(func.count()).select_from(UserModel))).scalar() or 0

            # Active missions via raw SQL (model may not be fully mapped)
            try:
                active_missions = (
                    await session.execute(
                        sa.text("SELECT count(*) FROM missions WHERE status IN ('ASSIGNED','IN_PROGRESS','PLANNED')")
                    )
                ).scalar() or 0
            except Exception:
                pass

            # Pending payments
            try:
                pending_payments = (
                    await session.execute(
                        select(func.count())
                        .select_from(PaymentIntentModel)
                        .where(PaymentIntentModel.status.in_(["PAYMENT_PENDING", "PENDING_ADMIN_REVIEW"]))
                    )
                ).scalar() or 0
            except Exception:
                pass

            # Completed (PAID)
            try:
                completed_analyses = (
                    await session.execute(
                        select(func.count()).select_from(PaymentIntentModel).where(PaymentIntentModel.status == "PAID")
                    )
                ).scalar() or 0
            except Exception:
                pass
    except Exception:
        pass  # DB connection issue — return zeros

    # KR-028: Pilotsuz ASSIGNED mission tespiti (orphan)
    orphan_assigned = 0
    try:
        async with get_async_session() as session:
            orphan_assigned = (
                await session.execute(
                    sa.text(
                        "SELECT count(*) FROM missions m "
                        "WHERE m.status = 'ASSIGNED' "
                        "AND NOT EXISTS (SELECT 1 FROM mission_assignments ma WHERE ma.mission_id = m.mission_id AND ma.is_current = true)"
                    )
                )
            ).scalar() or 0
    except Exception:
        pass

    return {
        "summary": {
            "total_fields": total_fields,
            "active_missions": active_missions,
            "completed_analyses": completed_analyses,
            "pending_payments": pending_payments,
            "total_users": total_users,
        },
        "warnings": {
            "orphan_assigned_missions": orphan_assigned,
            "orphan_message": f"{orphan_assigned} gorev ASSIGNED durumunda ama pilot atanmamis"
            if orphan_assigned > 0
            else None,
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
    """Admin SLA summary metrics — real data from payment lifecycle."""
    _require_admin(request)

    import sqlalchemy as sa

    compliance_rate = None
    try:
        async with get_async_session() as session:
            total_done = (
                await session.execute(
                    sa.text("SELECT count(*) FROM payment_intents WHERE status IN ('PAID','REJECTED')")
                )
            ).scalar() or 0
            pending = (
                await session.execute(
                    sa.text("SELECT count(*) FROM payment_intents WHERE status = 'PENDING_ADMIN_REVIEW'")
                )
            ).scalar() or 0
            if total_done + pending > 0:
                compliance_rate = round((total_done / (total_done + pending)) * 100, 1)
    except Exception:
        pass

    return {
        "review_start_sla_hours": 24,
        "decision_sla_hours": 48,
        "compliance_rate": compliance_rate,
    }


@router.get("/orphan-missions")
async def list_orphan_missions(request: Request) -> list[dict[str, Any]]:
    """KR-028: ASSIGNED durumunda olup pilot atanmamis mission'lari listele."""
    _require_admin(request)

    import sqlalchemy as sa

    orphans: list[dict[str, Any]] = []
    try:
        async with get_async_session() as session:
            result = await session.execute(
                sa.text(
                    "SELECT m.mission_id, m.field_id, m.crop_type, m.status, m.created_at, "
                    "f.province, f.district, f.area_donum "
                    "FROM missions m "
                    "JOIN fields f ON m.field_id = f.field_id "
                    "WHERE m.status = 'ASSIGNED' "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM mission_assignments ma "
                    "  WHERE ma.mission_id = m.mission_id AND ma.is_current = true"
                    ") "
                    "ORDER BY m.created_at DESC"
                )
            )
            for row in result.all():
                orphans.append(
                    {
                        "mission_id": str(row[0]),
                        "field_id": str(row[1]),
                        "crop_type": row[2],
                        "status": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "province": row[5],
                        "district": row[6],
                        "area_donum": float(row[7]) if row[7] else None,
                    }
                )
    except Exception:
        pass

    return orphans


@router.post("/assign-pilot")
async def admin_assign_pilot(request: Request) -> dict[str, str]:
    """KR-015: Admin manuel pilot atama — orphan mission'lari duzeltmek icin."""
    _require_admin(request)

    body = await request.json()
    mission_id_str = body.get("mission_id")
    pilot_id_str = body.get("pilot_id")

    if not mission_id_str or not pilot_id_str:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="mission_id ve pilot_id zorunlu")

    import uuid

    import sqlalchemy as sa

    from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
    from src.infrastructure.persistence.sqlalchemy.models.pilot_model import MissionAssignmentModel

    try:
        mission_uuid = uuid.UUID(mission_id_str)
        pilot_uuid = uuid.UUID(pilot_id_str)
    except ValueError:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Gecersiz UUID")

    async with get_async_session() as session:
        # Mission kontrol
        m_result = await session.execute(select(MissionModel).where(MissionModel.mission_id == mission_uuid))
        mission = m_result.scalar_one_or_none()
        if not mission:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Mission bulunamadi")

        # Mevcut atama var mi?
        existing = await session.execute(
            sa.text("SELECT 1 FROM mission_assignments WHERE mission_id = :mid AND is_current = true"),
            {"mid": mission_uuid},
        )
        if existing.scalar_one_or_none():
            return {"status": "already_assigned", "message": "Bu goreve zaten pilot atanmis."}

        # Atama olustur
        assignment = MissionAssignmentModel(
            mission_id=mission_uuid,
            pilot_id=pilot_uuid,
            assignment_type="ADMIN_OVERRIDE",
            is_current=True,
        )
        session.add(assignment)

        # Status'u ASSIGNED'a cek (zaten ASSIGNED ise degisiklik yok)
        if mission.status in ("PLANNED", "ASSIGNED"):
            mission.status = "ASSIGNED"

        await session.commit()

    import logging

    logging.getLogger("api.admin_dashboard").warning(
        "MISSION.ADMIN_ASSIGNED mission=%s pilot=%s", mission_uuid, pilot_uuid
    )

    return {"status": "assigned", "message": "Pilot basariyla atandi."}


@router.get("/province-stats")
async def get_province_stats(request: Request) -> dict[str, Any]:
    """KR-083: Il bazli istatistikler — tarla, abonelik, gorev, gelir, pilot."""
    _require_admin(request)

    import sqlalchemy as sa

    from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel
    from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel

    provinces_data: list[dict[str, Any]] = []

    try:
        async with get_async_session() as session:
            # Il bazli tarla sayilari
            field_rows = (
                await session.execute(
                    select(FieldModel.province, func.count().label("cnt")).group_by(FieldModel.province)
                )
            ).all()
            field_map = {row[0]: row[1] for row in field_rows}

            # Il bazli abonelik sayilari
            sub_map: dict[str, int] = {}
            try:
                sub_rows = (
                    await session.execute(
                        sa.text(
                            "SELECT f.province, count(s.subscription_id) "
                            "FROM subscriptions s JOIN fields f ON s.field_id = f.field_id "
                            "GROUP BY f.province"
                        )
                    )
                ).all()
                sub_map = {row[0]: row[1] for row in sub_rows}
            except Exception:
                pass

            # Il bazli gorev sayilari (aktif + tamamlanan)
            active_map: dict[str, int] = {}
            completed_map: dict[str, int] = {}
            try:
                mission_rows = (
                    await session.execute(
                        sa.text(
                            "SELECT f.province, m.status, count(*) "
                            "FROM missions m JOIN fields f ON m.field_id = f.field_id "
                            "GROUP BY f.province, m.status"
                        )
                    )
                ).all()
                for row in mission_rows:
                    prov, st, cnt = row[0], row[1], row[2]
                    if st in ("ASSIGNED", "ACKED", "FLOWN", "UPLOADED", "ANALYZING", "PLANNED"):
                        active_map[prov] = active_map.get(prov, 0) + cnt
                    elif st == "DONE":
                        completed_map[prov] = completed_map.get(prov, 0) + cnt
            except Exception:
                pass

            # Il bazli gelir (PAID odemeler)
            revenue_map: dict[str, int] = {}
            try:
                rev_rows = (
                    await session.execute(
                        sa.text(
                            "SELECT f.province, sum(p.amount_kurus) "
                            "FROM payment_intents p "
                            "JOIN missions m ON p.target_id = m.mission_id AND p.target_type = 'mission' "
                            "JOIN fields f ON m.field_id = f.field_id "
                            "WHERE p.status = 'PAID' "
                            "GROUP BY f.province"
                        )
                    )
                ).all()
                revenue_map = {row[0]: int(row[1] or 0) for row in rev_rows}
            except Exception:
                pass

            # Il bazli aktif pilot sayilari
            pilot_map: dict[str, int] = {}
            try:
                pilot_rows = (
                    await session.execute(
                        select(PilotModel.province, func.count().label("cnt"))
                        .where(PilotModel.is_active.is_(True))
                        .group_by(PilotModel.province)
                    )
                ).all()
                pilot_map = {row[0]: row[1] for row in pilot_rows}
            except Exception:
                pass

            # Tum illeri birlestir
            all_provinces = sorted(
                set(field_map.keys()) | set(sub_map.keys()) | set(active_map.keys()) | set(pilot_map.keys())
            )
            for prov in all_provinces:
                provinces_data.append(
                    {
                        "province": prov,
                        "total_fields": field_map.get(prov, 0),
                        "total_subscriptions": sub_map.get(prov, 0),
                        "active_missions": active_map.get(prov, 0),
                        "completed_missions": completed_map.get(prov, 0),
                        "total_revenue_kurus": revenue_map.get(prov, 0),
                        "active_pilots": pilot_map.get(prov, 0),
                    }
                )
    except Exception:
        pass

    return {"provinces": provinces_data}


__all__ = ["router"]
