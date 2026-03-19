# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-063: Admin audit log access — DB-backed query.
# KR-066: WORM audit_logs table (append-only).
"""Admin audit log query/export endpoints."""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, text

from src.infrastructure.persistence.sqlalchemy.models.audit_log_model import AuditLogModel
from src.infrastructure.persistence.sqlalchemy.session import get_async_session

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


class AuditLogItem(BaseModel):
    event_id: str
    occurred_at: datetime
    actor_subject: str | None = None
    action: str
    resource: str


class AuditLogQueryResponse(BaseModel):
    items: list[AuditLogItem]
    total: int


class AuditExportResponse(BaseModel):
    export_id: str
    status: str = "queued"


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles and "CENTRAL_ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/logs", response_model=AuditLogQueryResponse)
async def query_audit_logs(
    request: Request,
    action: str | None = Query(default=None, max_length=64),
    resource: str | None = Query(default=None, max_length=64),
    from_ts: datetime | None = Query(default=None),
    to_ts: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> AuditLogQueryResponse:
    """KR-066: Query audit logs from DB (WORM table)."""
    _require_admin(request)

    try:
        async with get_async_session() as session:
            stmt = select(AuditLogModel).order_by(AuditLogModel.ts.desc())

            if action:
                stmt = stmt.where(AuditLogModel.event_action == action)
            if resource:
                stmt = stmt.where(AuditLogModel.event_type == resource)
            if from_ts:
                stmt = stmt.where(AuditLogModel.ts >= from_ts)
            if to_ts:
                stmt = stmt.where(AuditLogModel.ts <= to_ts)

            # Count total
            count_stmt = select(func.count()).select_from(AuditLogModel)
            total = (await session.execute(count_stmt)).scalar() or 0

            # Paginate
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        items = [
            AuditLogItem(
                event_id=str(r.log_id),
                occurred_at=r.ts,
                actor_subject=r.actor_id_hash,
                action=f"{r.event_type}.{r.event_action}",
                resource=r.event_type,
            )
            for r in rows
        ]
        return AuditLogQueryResponse(items=items, total=total)
    except Exception:
        return AuditLogQueryResponse(items=[], total=0)


@router.post("/export", response_model=AuditExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_audit_logs(request: Request) -> AuditExportResponse:
    _require_admin(request)
    return AuditExportResponse(export_id=f"export-{_uuid.uuid4().hex[:8]}")


__all__ = ["router"]
