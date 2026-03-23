# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Mission management endpoints.
"""Mission management endpoints."""

from __future__ import annotations

import logging
import uuid as _uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

_LOGGER = logging.getLogger("api.missions")

# KR-028: Internal DB status → Contract enum mapping
# DB/domain: ACKED, FLOWN, ANALYZING, DONE
# Contract:  ACCEPTED, IN_PROGRESS, IN_ANALYSIS, DELIVERED
_STATUS_TO_CONTRACT: dict[str, str] = {
    "ACKED": "ACCEPTED",
    "FLOWN": "IN_PROGRESS",
    "ANALYZING": "IN_ANALYSIS",
    "DONE": "DELIVERED",
}


def _map_status(internal_status: str) -> str:
    """Map internal DB status to contract-canonical status."""
    return _STATUS_TO_CONTRACT.get(internal_status, internal_status)


router = APIRouter(prefix="/missions", tags=["missions"])


class MissionCreateRequest(BaseModel):
    field_id: str = Field(min_length=3, max_length=64)
    mission_date: date
    crop_type: str = Field(default="PAMUK", min_length=2, max_length=50)
    analysis_type: str = Field(default="MULTISPECTRAL", min_length=2, max_length=50)


class MissionResponse(BaseModel):
    mission_id: str
    field_id: str
    mission_date: date
    status: str
    crop_type: str | None = None
    analysis_type: str | None = None
    pilot_id: str | None = None
    subscription_id: str | None = None


def _require_authenticated(request: Request) -> tuple[str, _uuid.UUID]:
    """Extract subject and user_id (UUID) from JWT claims.

    KR-050: JWT her zaman user_id claim icerir (login + register + refresh).
    user_id yoksa token bozuk veya suresi dolmus demektir.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    subject = str(getattr(user, "subject", ""))
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    user_id_raw = getattr(user, "user_id", None)
    if not user_id_raw:
        _LOGGER.error("MISSION.AUTH user_id claim missing in JWT for subject=%s", subject)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum suresi dolmus — tekrar giris yapin",
        )
    try:
        return subject, _uuid.UUID(str(user_id_raw))
    except ValueError:
        _LOGGER.error("MISSION.AUTH invalid user_id=%s for subject=%s", user_id_raw, subject)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum suresi dolmus — tekrar giris yapin",
        )


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(request: Request, payload: MissionCreateRequest) -> MissionResponse:
    subject, user_id = _require_authenticated(request)

    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.mission_repository_impl import MissionRepositoryImpl

    try:
        field_id = _uuid.UUID(payload.field_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="field_id must be a valid UUID")

    mission_id = _uuid.uuid4()
    planned_at = datetime(
        payload.mission_date.year, payload.mission_date.month, payload.mission_date.day, tzinfo=timezone.utc
    )
    now = datetime.now(timezone.utc)
    payment_ref = f"PAY-{planned_at.strftime('%Y%m%d')}-{_uuid.uuid4().hex[:6].upper()}"

    try:
        async with get_async_session() as session:
            repo = MissionRepositoryImpl(session)
            await repo.save(
                mission_id=mission_id,
                field_id=field_id,
                user_id=user_id,
                crop_type=payload.crop_type,
                analysis_type=payload.analysis_type,
                planned_at=planned_at,
            )

            # KR-033: Auto-create payment_intent when mission is created
            from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
            from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
            import sqlalchemy as sa

            # KR-022: Calculate price via domain PricebookCalculator
            amount_kurus = 0
            try:
                field_result = await session.execute(
                    sa.select(FieldModel.area_m2, FieldModel.crop_type).where(FieldModel.field_id == field_id)
                )
                field_row = field_result.one_or_none()
                if field_row:
                    from src.application.services.pricing_service import calculate_single_price

                    crop_code = payload.crop_type or (field_row.crop_type if field_row.crop_type else "PAMUK")
                    amount_kurus = calculate_single_price(field_id, crop_code, float(field_row.area_m2))
            except Exception as exc:
                _LOGGER.warning("MISSION.PRICE_CALC_FAILED field=%s error=%s — using fallback", field_id, exc)

            # KR-022: Fiyat 0 ise fallback pricing config'den hesapla
            if amount_kurus == 0:
                try:
                    from src.presentation.api.v1.endpoints.admin_pricing import _read_config

                    cfg = _read_config()
                    crops_cfg = cfg.get("crops", [])
                    single_price: int | float = 15  # fallback: 15 TL/donum
                    if isinstance(crops_cfg, list):
                        for crop_cfg in crops_cfg:
                            if isinstance(crop_cfg, dict) and crop_cfg.get("code") == payload.crop_type:
                                single_price = float(crop_cfg.get("single_price", 15))
                                break
                    if field_row and field_row.area_m2:
                        area_donum = float(field_row.area_m2) / 1000.0
                        amount_kurus = max(100, int(float(single_price) * 100 * area_donum))
                    _LOGGER.warning("MISSION.PRICE_FALLBACK field=%s amount_kurus=%d", field_id, amount_kurus)
                except Exception as fallback_exc:
                    _LOGGER.warning("MISSION.PRICE_FALLBACK_FAILED field=%s error=%s", field_id, fallback_exc)

            # Look up price_snapshot if exists (best-effort, nullable FK)
            ps_row = None
            try:
                ps_result = await session.execute(sa.text("SELECT price_snapshot_id FROM price_snapshots LIMIT 1"))
                ps_row = ps_result.scalar_one_or_none()
            except Exception:
                _LOGGER.warning("MISSION.CREATE price_snapshots lookup failed — continuing without snapshot")

            payment_intent_id = _uuid.uuid4()
            intent = PaymentIntentModel(
                payment_intent_id=payment_intent_id,
                payer_user_id=user_id,
                target_type="MISSION",
                target_id=mission_id,
                amount_kurus=amount_kurus,
                currency="TRY",
                method="IBAN_TRANSFER",
                status="PAYMENT_PENDING",
                payment_ref=payment_ref,
                price_snapshot_id=ps_row,
                created_at=now,
                updated_at=now,
            )
            session.add(intent)

            # Link mission to payment intent
            await session.execute(
                sa.text("UPDATE missions SET payment_intent_id = :pi_id WHERE mission_id = :m_id"),
                {"pi_id": payment_intent_id, "m_id": mission_id},
            )

            await session.commit()

        _LOGGER.info(
            "MISSION.CREATED mission=%s user=%s field=%s intent=%s", mission_id, user_id, field_id, payment_intent_id
        )

    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.error("MISSION.CREATE_FAILED user=%s field=%s error=%s", user_id, field_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analiz talebi olusturulamadi. Lutfen tekrar deneyin.",
        ) from exc

    return MissionResponse(
        mission_id=str(mission_id),
        field_id=payload.field_id,
        mission_date=payload.mission_date,
        status="PLANNED",
        crop_type=payload.crop_type,
        analysis_type=payload.analysis_type,
    )


@router.get("", response_model=list[MissionResponse])
async def list_missions(request: Request) -> list[MissionResponse]:
    subject, user_id = _require_authenticated(request)

    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.mission_repository_impl import MissionRepositoryImpl

    async with get_async_session() as session:
        repo = MissionRepositoryImpl(session)
        models = await repo.list_by_user_id(user_id)

    return [
        MissionResponse(
            mission_id=str(m.mission_id),
            field_id=str(m.field_id),
            mission_date=(m.planned_at or m.created_at).date(),
            status=_map_status(m.status),
            crop_type=m.crop_type,
            analysis_type=m.analysis_type,
            subscription_id=str(m.subscription_id) if m.subscription_id else None,
        )
        for m in models
    ]
