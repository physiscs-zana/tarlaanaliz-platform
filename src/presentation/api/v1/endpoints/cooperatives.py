# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-014: Kooperatif / Uretici Birligi yonetim endpoint'leri.
# KR-063: COOP_OWNER, COOP_ADMIN, CENTRAL_ADMIN rolleri.
"""Cooperative management, invite, membership, dashboard endpoints (KR-014)."""

from __future__ import annotations

import csv
import io
import logging
import random
import string
import uuid as _uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.sqlalchemy.models.cooperative_model import (
    CoopInviteModel,
    CoopMembershipModel,
    CooperativeModel,
)
from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

LOGGER = logging.getLogger("api.cooperatives")

router = APIRouter(tags=["cooperatives"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CooperativeCreateRequest(BaseModel):
    """KR-014: Kooperatif olusturma istegi."""

    name: str = Field(min_length=2, max_length=255)
    province: str = Field(min_length=2, max_length=100)
    district: str | None = Field(default=None, max_length=100)


class CooperativeResponse(BaseModel):
    """KR-014: Kooperatif yanit modeli."""

    coop_id: str
    name: str
    province: str
    district: str | None = None
    status: str
    owner_display_name: str | None = None
    member_count: int = 0
    created_at: str


class InviteGenerateRequest(BaseModel):
    """KR-014: Davet kodu olusturma istegi."""

    org_type: str = "COOP"


class JoinRequest(BaseModel):
    """KR-014: Davet koduyla katilma istegi."""

    invite_code: str = Field(min_length=6, max_length=6)


class MemberResponse(BaseModel):
    """KR-014: Uye yanit modeli."""

    id: str
    name: str
    phone: str
    status: str
    role: str


class CoopFieldResponse(BaseModel):
    """KR-014: Kooperatif tarlasi yanit modeli."""

    field_id: str
    owner_name: str
    province: str
    district: str
    village: str
    block_no: str
    parcel_no: str
    area_donum: float
    crop_type: str | None = None


class DashboardResponse(BaseModel):
    """KR-014: Dashboard KPI yaniti."""

    member_count: int
    field_count: int
    mission_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COOP_MANAGEMENT_ROLES = {"COOP_OWNER", "COOP_ADMIN"}
_COOP_ALL_ROLES = {"COOP_OWNER", "COOP_ADMIN", "COOP_AGRONOMIST", "COOP_VIEWER"}


def _get_user_id(request: Request) -> _uuid.UUID:
    """Extract authenticated user_id from JWT middleware."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    uid = getattr(user, "user_id", None) or getattr(user, "subject", None)
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return _uuid.UUID(str(uid))


def _get_user_roles(request: Request) -> set[str]:
    """Extract user roles from JWT middleware."""
    return set(getattr(request.state, "roles", []))


def _require_roles(request: Request, allowed: set[str]) -> _uuid.UUID:
    """Require at least one of the allowed roles. Return user_id."""
    user_id = _get_user_id(request)
    roles = _get_user_roles(request)
    if not roles.intersection(allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user_id


def _require_central_admin(request: Request) -> _uuid.UUID:
    """Require CENTRAL_ADMIN role."""
    return _require_roles(request, {"CENTRAL_ADMIN"})


def _mask_phone(phone: str | None) -> str:
    """KR-050: Telefon numarasini maskele. 05XX XXX XX34 formati."""
    if not phone or len(phone) < 4:
        return "---"
    return phone[:4] + " XXX XX" + phone[-2:]


def _generate_invite_code() -> str:
    """6 haneli rastgele davet kodu."""
    return "".join(random.choices(string.digits, k=6))


# ---------------------------------------------------------------------------
# 1. POST /cooperatives — Kooperatif olustur
# ---------------------------------------------------------------------------


@router.post("/cooperatives", status_code=status.HTTP_201_CREATED)
async def create_cooperative(request: Request, payload: CooperativeCreateRequest) -> CooperativeResponse:
    """KR-014: Kooperatif olustur. Durum PENDING_APPROVAL olarak baslar."""
    user_id = _get_user_id(request)

    async with get_async_session() as session:
        # Kullanicinin zaten bir kooperatifi var mi?
        existing = await session.execute(
            select(CoopMembershipModel.coop_id).where(CoopMembershipModel.user_id == user_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Zaten bir kooperatife uyesiniz.",
            )

        coop_id = _uuid.uuid4()
        now = datetime.now(timezone.utc)

        coop = CooperativeModel(
            coop_id=coop_id,
            name=payload.name.strip(),
            province=payload.province.strip(),
            district=payload.district.strip() if payload.district else None,
            owner_user_id=user_id,
            status="PENDING_APPROVAL",
            created_at=now,
            updated_at=now,
        )
        session.add(coop)

        # Owner otomatik uyelik (is_confirmed=True)
        membership = CoopMembershipModel(
            membership_id=_uuid.uuid4(),
            coop_id=coop_id,
            user_id=user_id,
            is_confirmed=True,
            confirmed_at=now,
        )
        session.add(membership)

        # COOP_OWNER rolu ekle
        role_model = UserRoleModel(
            user_role_id=_uuid.uuid4(),
            user_id=user_id,
            role="COOP_OWNER",
            granted_at=now,
        )
        session.add(role_model)

        await session.commit()

    LOGGER.warning("COOP.CREATED coop_id=%s owner=%s name=%s", coop_id, user_id, payload.name)

    return CooperativeResponse(
        coop_id=str(coop_id),
        name=payload.name,
        province=payload.province,
        district=payload.district,
        status="PENDING_APPROVAL",
        member_count=1,
        created_at=now.isoformat(),
    )


# ---------------------------------------------------------------------------
# 2. GET /cooperatives/my — Kendi kooperatifimi getir
# ---------------------------------------------------------------------------


@router.get("/cooperatives/my")
async def get_my_cooperative(request: Request) -> CooperativeResponse:
    """KR-014: Kullanicinin kooperatifini getir."""
    user_id = _get_user_id(request)

    async with get_async_session() as session:
        membership = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = membership.scalar_one_or_none()
        if coop_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kooperatif bulunamadi")

        result = await session.execute(
            select(CooperativeModel)
            .options(selectinload(CooperativeModel.owner))
            .where(CooperativeModel.coop_id == coop_id)
        )
        coop = result.scalar_one_or_none()
        if coop is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kooperatif bulunamadi")

        member_count_result = await session.execute(
            select(func.count())
            .select_from(CoopMembershipModel)
            .where(
                CoopMembershipModel.coop_id == coop_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        member_count = member_count_result.scalar() or 0

    owner_name = None
    if coop.owner:
        owner_name = coop.owner.display_name or f"{coop.owner.first_name} {coop.owner.last_name}".strip() or None

    return CooperativeResponse(
        coop_id=str(coop.coop_id),
        name=coop.name,
        province=coop.province,
        district=coop.district,
        status=coop.status,
        owner_display_name=owner_name,
        member_count=int(member_count),
        created_at=coop.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# 3. POST /cooperatives/{coop_id}/approve — Central Admin onayi
# ---------------------------------------------------------------------------


@router.post("/cooperatives/{coop_id}/approve")
async def approve_cooperative(request: Request, coop_id: str) -> CooperativeResponse:
    """KR-014: Central Admin kooperatifi onaylar (PENDING_APPROVAL -> ACTIVE)."""
    admin_id = _require_central_admin(request)

    try:
        coop_uuid = _uuid.UUID(coop_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid coop_id") from exc

    async with get_async_session() as session:
        result = await session.execute(select(CooperativeModel).where(CooperativeModel.coop_id == coop_uuid))
        coop = result.scalar_one_or_none()
        if coop is None:
            raise HTTPException(status_code=404, detail="Kooperatif bulunamadi")
        if coop.status == "ACTIVE":
            return CooperativeResponse(
                coop_id=str(coop.coop_id),
                name=coop.name,
                province=coop.province,
                district=coop.district,
                status=coop.status,
                created_at=coop.created_at.isoformat(),
            )

        now = datetime.now(timezone.utc)
        coop.status = "ACTIVE"
        coop.approved_by = admin_id
        coop.approved_at = now
        coop.updated_at = now
        await session.commit()

    LOGGER.warning("COOP.APPROVED coop_id=%s by=%s", coop_uuid, admin_id)

    return CooperativeResponse(
        coop_id=str(coop.coop_id),
        name=coop.name,
        province=coop.province,
        district=coop.district,
        status="ACTIVE",
        created_at=coop.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# 4. POST /coop/invites/generate — Davet kodu olustur
# ---------------------------------------------------------------------------


@router.post("/coop/invites/generate")
async def generate_invite(request: Request, payload: InviteGenerateRequest) -> dict[str, str]:
    """KR-014: 6 haneli davet kodu olustur."""
    user_id = _require_roles(request, _COOP_MANAGEMENT_ROLES | {"CENTRAL_ADMIN"})

    async with get_async_session() as session:
        # Kullanicinin kooperatifini bul
        mem = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = mem.scalar_one_or_none()
        if coop_id is None:
            raise HTTPException(status_code=404, detail="Kooperatif bulunamadi")

        # Benzersiz kod uret (maks 5 deneme)
        code = ""
        for _ in range(5):
            candidate = _generate_invite_code()
            exists = await session.execute(
                select(CoopInviteModel.invite_id).where(
                    CoopInviteModel.invite_code == candidate,
                    CoopInviteModel.status == "ACTIVE",
                )
            )
            if exists.scalar_one_or_none() is None:
                code = candidate
                break
        if not code:
            raise HTTPException(status_code=500, detail="Davet kodu uretilemedi. Tekrar deneyin.")

        invite = CoopInviteModel(
            invite_id=_uuid.uuid4(),
            coop_id=coop_id,
            invite_code=code,
            status="ACTIVE",
            created_by=user_id,
        )
        session.add(invite)
        await session.commit()

    LOGGER.warning("COOP.INVITE_GENERATED coop_id=%s code=%s by=%s", coop_id, code, user_id)
    return {"code": code}


# ---------------------------------------------------------------------------
# 5. GET /coop/invites — Davet listesi
# ---------------------------------------------------------------------------


@router.get("/coop/invites")
async def list_invites(request: Request) -> dict[str, list[dict[str, str]]]:
    """KR-014: Aktif davet kodlarini listele."""
    user_id = _require_roles(request, _COOP_MANAGEMENT_ROLES | {"CENTRAL_ADMIN"})

    async with get_async_session() as session:
        mem = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = mem.scalar_one_or_none()
        if coop_id is None:
            return {"items": []}

        result = await session.execute(
            select(CoopInviteModel)
            .where(CoopInviteModel.coop_id == coop_id)
            .order_by(CoopInviteModel.created_at.desc())
        )
        invites = result.scalars().all()

    return {
        "items": [
            {
                "code": inv.invite_code,
                "org_type": "COOP",
                "created_at": inv.created_at.isoformat(),
                "status": inv.status,
            }
            for inv in invites
        ]
    }


# ---------------------------------------------------------------------------
# 6. POST /coop/invites/bulk-import — CSV toplu import
# ---------------------------------------------------------------------------


@router.post("/coop/invites/bulk-import")
async def bulk_import_invites(
    request: Request,
    file: UploadFile = File(...),
    org_type: str = Form(default="COOP"),
) -> dict[str, object]:
    """KR-014: CSV toplu davet kodu olusturma. Sutunlar: ad, soyad, telefon."""
    user_id = _require_roles(request, _COOP_MANAGEMENT_ROLES | {"CENTRAL_ADMIN"})

    # Dosya boyutu kontrolu (5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Dosya boyutu 5MB'i asamaz.")

    async with get_async_session() as session:
        mem = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = mem.scalar_one_or_none()
        if coop_id is None:
            raise HTTPException(status_code=404, detail="Kooperatif bulunamadi")

        # CSV parse
        imported = 0
        errors: list[str] = []
        try:
            text_content = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text_content))
            for row_num, row in enumerate(reader, start=2):
                ad = (row.get("ad") or "").strip()
                soyad = (row.get("soyad") or "").strip()
                telefon = (row.get("telefon") or "").strip()

                if not ad or not telefon:
                    errors.append(f"Satir {row_num}: ad veya telefon eksik")
                    continue

                code = _generate_invite_code()
                invite = CoopInviteModel(
                    invite_id=_uuid.uuid4(),
                    coop_id=coop_id,
                    invite_code=code,
                    status="ACTIVE",
                    created_by=user_id,
                )
                session.add(invite)
                imported += 1
        except UnicodeDecodeError:
            raise HTTPException(status_code=422, detail="Dosya UTF-8 formatinda olmali.")

        await session.commit()

    LOGGER.warning("COOP.BULK_IMPORT coop_id=%s imported=%d errors=%d by=%s", coop_id, imported, len(errors), user_id)
    return {"imported": imported, "errors": errors}


# ---------------------------------------------------------------------------
# 7. POST /coop/join — Davet koduyla katil
# ---------------------------------------------------------------------------


@router.post("/coop/join")
async def join_cooperative(request: Request, payload: JoinRequest) -> dict[str, str]:
    """KR-014: Ciftci davet koduyla kooperatife katilir."""
    user_id = _get_user_id(request)

    async with get_async_session() as session:
        # Zaten uye mi?
        existing_mem = await session.execute(
            select(CoopMembershipModel.membership_id).where(CoopMembershipModel.user_id == user_id)
        )
        if existing_mem.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Zaten bir kooperatife uyesiniz.")

        # Davet kodunu bul
        invite_result = await session.execute(
            select(CoopInviteModel).where(
                CoopInviteModel.invite_code == payload.invite_code,
                CoopInviteModel.status == "ACTIVE",
            )
        )
        invite = invite_result.scalar_one_or_none()
        if invite is None:
            raise HTTPException(status_code=404, detail="Gecersiz veya suresi dolmus davet kodu.")

        # Kooperatif aktif mi?
        coop_result = await session.execute(
            select(CooperativeModel.status).where(CooperativeModel.coop_id == invite.coop_id)
        )
        coop_status = coop_result.scalar_one_or_none()
        if coop_status != "ACTIVE":
            raise HTTPException(status_code=409, detail="Kooperatif henuz aktif degil.")

        now = datetime.now(timezone.utc)

        # Uyelik olustur
        membership = CoopMembershipModel(
            membership_id=_uuid.uuid4(),
            coop_id=invite.coop_id,
            user_id=user_id,
            invite_code=payload.invite_code,
            is_confirmed=True,
            confirmed_at=now,
        )
        session.add(membership)

        # Daveti USED yap
        invite.status = "USED"

        # FARMER_MEMBER rolunu ekle (yoksa)
        existing_role = await session.execute(
            select(UserRoleModel.user_role_id).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role == "FARMER_MEMBER",
            )
        )
        if existing_role.scalar_one_or_none() is None:
            role_model = UserRoleModel(
                user_role_id=_uuid.uuid4(),
                user_id=user_id,
                role="FARMER_MEMBER",
                granted_at=now,
            )
            session.add(role_model)

        await session.commit()

    LOGGER.warning("COOP.MEMBER_JOINED coop_id=%s user_id=%s code=%s", invite.coop_id, user_id, payload.invite_code)
    return {"status": "joined", "message": "Kooperatife basariyla katildiniz."}


# ---------------------------------------------------------------------------
# 8. GET /coop/members — Uye listesi
# ---------------------------------------------------------------------------


@router.get("/coop/members")
async def list_members(request: Request) -> list[MemberResponse]:
    """KR-014: Kooperatif uyelerini listele."""
    user_id = _require_roles(request, _COOP_ALL_ROLES | {"CENTRAL_ADMIN"})

    async with get_async_session() as session:
        mem = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = mem.scalar_one_or_none()
        if coop_id is None:
            return []

        result = await session.execute(
            select(CoopMembershipModel)
            .options(selectinload(CoopMembershipModel.user))
            .where(
                CoopMembershipModel.coop_id == coop_id,
            )
            .order_by(CoopMembershipModel.created_at)
        )
        memberships = result.scalars().unique().all()

        # Uye rollerini toplu cek
        user_ids = [m.user_id for m in memberships]
        role_result = await session.execute(
            select(UserRoleModel.user_id, UserRoleModel.role).where(UserRoleModel.user_id.in_(user_ids))
        )
        user_roles: dict[_uuid.UUID, str] = {}
        coop_role_priority = ["COOP_OWNER", "COOP_ADMIN", "COOP_AGRONOMIST", "COOP_VIEWER", "FARMER_MEMBER"]
        for uid, role in role_result.all():
            current = user_roles.get(uid)
            if (
                current is None or coop_role_priority.index(role) < coop_role_priority.index(current)
                if role in coop_role_priority and current in coop_role_priority
                else False
            ):
                user_roles[uid] = role

    members: list[MemberResponse] = []
    for m in memberships:
        u = m.user
        name = ""
        phone = "---"
        if u:
            name = u.display_name or f"{u.first_name} {u.last_name}".strip() or ""
            phone = _mask_phone(u.phone)

        member_status = "ACTIVE" if m.is_confirmed else "PENDING"
        role = user_roles.get(m.user_id, "FARMER_MEMBER")

        members.append(
            MemberResponse(
                id=str(m.user_id),
                name=name,
                phone=phone,
                status=member_status,
                role=role,
            )
        )

    return members


# ---------------------------------------------------------------------------
# 9. GET /coop/fields — Kooperatif tarlalari
# ---------------------------------------------------------------------------


@router.get("/coop/fields")
async def list_coop_fields(request: Request) -> list[CoopFieldResponse]:
    """KR-014: Kooperatif uyelerinin tarlalarini listele."""
    user_id = _require_roles(request, (_COOP_ALL_ROLES - {"COOP_VIEWER"}) | {"CENTRAL_ADMIN"})

    async with get_async_session() as session:
        mem = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = mem.scalar_one_or_none()
        if coop_id is None:
            return []

        # Uye user_id'lerini bul
        member_result = await session.execute(
            select(CoopMembershipModel.user_id).where(
                CoopMembershipModel.coop_id == coop_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        member_ids = [row[0] for row in member_result.all()]

        if not member_ids:
            return []

        # Uye tarlalarini cek (user_id ile VEYA coop_id ile)
        field_result = await session.execute(
            select(FieldModel, UserModel.display_name, UserModel.first_name, UserModel.last_name)
            .join(UserModel, FieldModel.user_id == UserModel.user_id)
            .where(FieldModel.user_id.in_(member_ids))
            .order_by(FieldModel.province, FieldModel.district)
        )
        rows = field_result.all()

    fields: list[CoopFieldResponse] = []
    for f, display_name, first_name, last_name in rows:
        owner_name = display_name or f"{first_name} {last_name}".strip() or "---"
        fields.append(
            CoopFieldResponse(
                field_id=str(f.field_id),
                owner_name=owner_name,
                province=f.province,
                district=f.district,
                village=f.village,
                block_no=f.block_no,
                parcel_no=f.parcel_no,
                area_donum=float(f.area_donum),
                crop_type=f.crop_type,
            )
        )

    return fields


# ---------------------------------------------------------------------------
# 10. GET /coop/dashboard — Dashboard KPI'lar
# ---------------------------------------------------------------------------


@router.get("/coop/dashboard")
async def get_dashboard(request: Request) -> DashboardResponse:
    """KR-014: Kooperatif dashboard — uye sayisi, tarla sayisi, aktif gorev sayisi."""
    user_id = _require_roles(request, _COOP_MANAGEMENT_ROLES | {"CENTRAL_ADMIN"})

    async with get_async_session() as session:
        mem = await session.execute(
            select(CoopMembershipModel.coop_id).where(
                CoopMembershipModel.user_id == user_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        coop_id = mem.scalar_one_or_none()
        if coop_id is None:
            return DashboardResponse(member_count=0, field_count=0, mission_count=0)

        # Uye sayisi
        member_count_result = await session.execute(
            select(func.count())
            .select_from(CoopMembershipModel)
            .where(
                CoopMembershipModel.coop_id == coop_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        member_count = member_count_result.scalar() or 0

        # Uye ID'leri
        member_ids_result = await session.execute(
            select(CoopMembershipModel.user_id).where(
                CoopMembershipModel.coop_id == coop_id,
                CoopMembershipModel.is_confirmed.is_(True),
            )
        )
        member_ids = [row[0] for row in member_ids_result.all()]

        # Tarla sayisi
        field_count = 0
        mission_count = 0
        if member_ids:
            fc_result = await session.execute(
                select(func.count()).select_from(FieldModel).where(FieldModel.user_id.in_(member_ids))
            )
            field_count = fc_result.scalar() or 0

            # Aktif gorev sayisi
            field_ids_result = await session.execute(
                select(FieldModel.field_id).where(FieldModel.user_id.in_(member_ids))
            )
            field_ids = [row[0] for row in field_ids_result.all()]

            if field_ids:
                mc_result = await session.execute(
                    select(func.count())
                    .select_from(MissionModel)
                    .where(
                        MissionModel.field_id.in_(field_ids),
                        MissionModel.status.notin_(["DONE", "FAILED", "CANCELLED"]),
                    )
                )
                mission_count = mc_result.scalar() or 0

    return DashboardResponse(
        member_count=int(member_count),
        field_count=int(field_count),
        mission_count=int(mission_count),
    )


__all__ = ["router"]
