# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-031: Pilot hakediş endpoint'leri — aylık kazanç, il bazlı ücret, itiraz.
"""Pilot earnings endpoints — payroll, rates, disputes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from src.infrastructure.persistence.sqlalchemy.models.pilot_earning_model import (
    PilotEarningModel,
    PilotRateByProvinceModel,
)
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

router = APIRouter(prefix="/pilot-earnings", tags=["pilot-earnings"])


# --- Schemas ---


class PilotEarningResponse(BaseModel):
    earning_id: str
    mission_id: str
    period_month: str
    area_donum: int
    rate_per_donum_kurus: int
    amount_kurus: int
    province: str
    status: str
    disputed_at: str | None
    dispute_reason: str | None
    approved_at: str | None
    paid_at: str | None


class PilotEarningSummaryResponse(BaseModel):
    period_month: str
    total_missions: int
    total_area_donum: int
    total_amount_kurus: int
    status_breakdown: dict[str, int]


class DisputeRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=500)


class ProvinceRateResponse(BaseModel):
    province: str
    rate_per_donum_kurus: int
    effective_from: str


class ProvinceRateCreateRequest(BaseModel):
    province: str = Field(min_length=2, max_length=100)
    rate_per_donum_kurus: int = Field(ge=100, le=10000)  # 1-100 TL arası


# --- Helpers ---


def _require_pilot(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "PILOT" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pilot rolü gerekli")
    return str(getattr(user, "subject", ""))


def _require_admin(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "CENTRAL_ADMIN" not in roles and "BILLING_ADMIN" not in roles and "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return str(getattr(user, "subject", ""))


# --- Pilot endpoints ---


@router.get("/my", response_model=list[PilotEarningResponse])
async def list_my_earnings(
    request: Request,
    period_month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> list[PilotEarningResponse]:
    """Pilotun kendi hakediş listesi."""
    pilot_subject = _require_pilot(request)

    async with get_async_session() as session:
        # pilot_id'yi user subject'ten bul
        from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel
        from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel

        user_q = await session.execute(select(UserModel.user_id).where(UserModel.phone == pilot_subject))
        user_row = user_q.first()
        if not user_row:
            return []

        pilot_q = await session.execute(select(PilotModel.pilot_id).where(PilotModel.user_id == user_row[0]))
        pilot_row = pilot_q.first()
        if not pilot_row:
            return []

        stmt = select(PilotEarningModel).where(PilotEarningModel.pilot_id == pilot_row[0])
        if period_month:
            stmt = stmt.where(PilotEarningModel.period_month == period_month)
        stmt = stmt.order_by(PilotEarningModel.created_at.desc()).limit(100)

        result = await session.execute(stmt)
        return [
            PilotEarningResponse(
                earning_id=str(m.earning_id),
                mission_id=str(m.mission_id),
                period_month=m.period_month,
                area_donum=m.area_donum,
                rate_per_donum_kurus=m.rate_per_donum_kurus,
                amount_kurus=m.amount_kurus,
                province=m.province,
                status=m.status,
                disputed_at=m.disputed_at.isoformat() if m.disputed_at else None,
                dispute_reason=m.dispute_reason,
                approved_at=m.approved_at.isoformat() if m.approved_at else None,
                paid_at=m.paid_at.isoformat() if m.paid_at else None,
            )
            for m in result.scalars().all()
        ]


@router.post("/{earning_id}/dispute", status_code=status.HTTP_200_OK)
async def dispute_earning(request: Request, earning_id: str, payload: DisputeRequest) -> dict[str, str]:
    """Pilot hakediş itirazı — 3 iş günü penceresi (KR-031)."""
    _require_pilot(request)

    async with get_async_session() as session:
        import uuid

        model = await session.get(PilotEarningModel, uuid.UUID(earning_id))
        if model is None:
            raise HTTPException(status_code=404, detail="Hakediş kaydı bulunamadı")
        if model.status != "PENDING":
            raise HTTPException(status_code=409, detail="Sadece PENDING durumundaki hakediş itiraz edilebilir")

        # 3 iş günü kontrolü (oluşturulma tarihinden itibaren)
        days_since = (datetime.now(timezone.utc) - model.created_at).days
        if days_since > 5:  # 3 iş günü ≈ 5 takvim günü (güvenli marj)
            raise HTTPException(status_code=409, detail="İtiraz süresi dolmuş (3 iş günü)")

        model.status = "DISPUTED"
        model.dispute_reason = payload.reason
        model.disputed_at = datetime.now(timezone.utc)
        await session.commit()

        return {"status": "DISPUTED", "earning_id": earning_id}


# --- Admin endpoints ---


@router.get("/admin/summary", response_model=list[PilotEarningSummaryResponse])
async def admin_earnings_summary(
    request: Request,
    period_month: str = Query(pattern=r"^\d{4}-\d{2}$"),
) -> list[PilotEarningSummaryResponse]:
    """Admin: dönem bazlı hakediş özeti."""
    _require_admin(request)

    async with get_async_session() as session:
        stmt = (
            select(
                PilotEarningModel.period_month,
                PilotEarningModel.status,
                func.count().label("cnt"),
                func.sum(PilotEarningModel.area_donum).label("total_area"),
                func.sum(PilotEarningModel.amount_kurus).label("total_amount"),
            )
            .where(PilotEarningModel.period_month == period_month)
            .group_by(PilotEarningModel.period_month, PilotEarningModel.status)
        )
        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        status_breakdown: dict[str, int] = {}
        total_missions = 0
        total_area = 0
        total_amount = 0
        for row in rows:
            status_breakdown[row.status] = row.cnt
            total_missions += row.cnt
            total_area += row.total_area or 0
            total_amount += row.total_amount or 0

        return [
            PilotEarningSummaryResponse(
                period_month=period_month,
                total_missions=total_missions,
                total_area_donum=total_area,
                total_amount_kurus=total_amount,
                status_breakdown=status_breakdown,
            )
        ]


@router.get("/rates", response_model=list[ProvinceRateResponse])
async def list_province_rates(request: Request) -> list[ProvinceRateResponse]:
    """İl bazlı pilot ücretlerini listele."""
    _require_admin(request)

    async with get_async_session() as session:
        result = await session.execute(select(PilotRateByProvinceModel).order_by(PilotRateByProvinceModel.province))
        return [
            ProvinceRateResponse(
                province=m.province,
                rate_per_donum_kurus=m.rate_per_donum_kurus,
                effective_from=m.effective_from.isoformat(),
            )
            for m in result.scalars().all()
        ]


@router.post("/rates", response_model=ProvinceRateResponse, status_code=status.HTTP_201_CREATED)
async def set_province_rate(request: Request, payload: ProvinceRateCreateRequest) -> ProvinceRateResponse:
    """İl bazlı pilot ücret tanımla/güncelle — CENTRAL_ADMIN."""
    _require_admin(request)

    async with get_async_session() as session:
        existing = await session.execute(
            select(PilotRateByProvinceModel).where(PilotRateByProvinceModel.province == payload.province)
        )
        model = existing.scalar_one_or_none()

        if model:
            model.rate_per_donum_kurus = payload.rate_per_donum_kurus
            model.effective_from = datetime.now(timezone.utc)
        else:
            model = PilotRateByProvinceModel()
            model.province = payload.province
            model.rate_per_donum_kurus = payload.rate_per_donum_kurus
            session.add(model)

        await session.commit()
        await session.refresh(model)

        return ProvinceRateResponse(
            province=model.province,
            rate_per_donum_kurus=model.rate_per_donum_kurus,
            effective_from=model.effective_from.isoformat(),
        )
