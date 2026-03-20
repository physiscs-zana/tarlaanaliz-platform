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


def _require_authenticated(request: Request) -> tuple[str, str]:
    """Extract authenticated user_id. Raises 401 if missing."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    # Try user_id first (set by JWT middleware), fall back to subject
    user_id = getattr(user, "user_id", None) or getattr(user, "subject", None)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    subject = str(getattr(user, "subject", ""))
    return subject, str(user_id)


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(request: Request, payload: MissionCreateRequest) -> MissionResponse:
    subject, user_id_str = _require_authenticated(request)

    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.mission_repository_impl import MissionRepositoryImpl

    try:
        user_id = _uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        _LOGGER.error("MISSION.CREATE invalid user_id=%s", user_id_str)
        raise HTTPException(status_code=401, detail="Gecersiz kullanici kimlik bilgisi")

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

            # Calculate price from field area and pricing config
            amount_kurus = 0
            try:
                field_result = await session.execute(
                    sa.select(FieldModel.area_m2, FieldModel.crop_type).where(FieldModel.field_id == field_id)
                )
                field_row = field_result.one_or_none()
                if field_row:
                    from src.presentation.api.v1.endpoints.admin_pricing import _read_config

                    cfg = _read_config()
                    crops = cfg.get("crops", [])
                    crop_code = payload.crop_type or (field_row.crop_type if field_row.crop_type else "PAMUK")
                    crop_cfg = next((c for c in crops if c.get("code") == crop_code), None)
                    if crop_cfg:
                        area_ha = float(field_row.area_m2) / 10000
                        price_per_ha = crop_cfg.get("single_price", 250)
                        amount_kurus = round(area_ha * price_per_ha * 100)
            except Exception as exc:
                _LOGGER.warning("MISSION.PRICE_CALC_FAILED field=%s error=%s", field_id, exc)

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
    subject, user_id_str = _require_authenticated(request)

    from src.infrastructure.persistence.sqlalchemy.session import get_async_session
    from src.infrastructure.persistence.sqlalchemy.repositories.mission_repository_impl import MissionRepositoryImpl

    try:
        user_id = _uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        return []

    async with get_async_session() as session:
        repo = MissionRepositoryImpl(session)
        models = await repo.list_by_user_id(user_id)

    return [
        MissionResponse(
            mission_id=str(m.mission_id),
            field_id=str(m.field_id),
            mission_date=(m.planned_at or m.created_at).date(),
            status=m.status,
            crop_type=m.crop_type,
            analysis_type=m.analysis_type,
        )
        for m in models
    ]
