# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Admin audit log query/export endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

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


class AuditQueryFilter(BaseModel):
    action: str | None = Field(default=None, max_length=64)
    resource: str | None = Field(default=None, max_length=64)
    from_ts: datetime | None = None
    to_ts: datetime | None = None


class AdminAuditService(Protocol):
    def query(self, flt: AuditQueryFilter, limit: int, offset: int) -> AuditLogQueryResponse: ...

    def queue_export(self, flt: AuditQueryFilter) -> AuditExportResponse: ...


@dataclass(slots=True)
class _InMemoryAdminAuditService:
    def query(self, flt: AuditQueryFilter, limit: int, offset: int) -> AuditLogQueryResponse:
        _ = flt
        return AuditLogQueryResponse(items=[], total=0)

    def queue_export(self, flt: AuditQueryFilter) -> AuditExportResponse:
        _ = flt
        return AuditExportResponse(export_id="audit-export-queued")


def get_admin_audit_service() -> AdminAuditService:
    return _InMemoryAdminAuditService()


def _require_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    roles = set(getattr(request.state, "roles", []))
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/logs", response_model=AuditLogQueryResponse)
def query_audit_logs(
    request: Request,
    action: str | None = Query(default=None, max_length=64),
    resource: str | None = Query(default=None, max_length=64),
    from_ts: datetime | None = Query(default=None),
    to_ts: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: AdminAuditService = Depends(get_admin_audit_service),
) -> AuditLogQueryResponse:
    # KR-033: audit flow visibility at admin surface.
    _require_admin(request)
    filters = AuditQueryFilter(action=action, resource=resource, from_ts=from_ts, to_ts=to_ts)
    return service.query(filters, limit=limit, offset=offset)


@router.post("/export", response_model=AuditExportResponse, status_code=status.HTTP_202_ACCEPTED)
def export_audit_logs(
    request: Request,
    filters: AuditQueryFilter,
    service: AdminAuditService = Depends(get_admin_audit_service),
) -> AuditExportResponse:
    _require_admin(request)
    return service.queue_export(filters)
