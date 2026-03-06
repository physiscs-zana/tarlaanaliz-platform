# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""FastAPI dependency wiring and HTTP-layer hooks."""

from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Protocol
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# NOTE: This is a presentation-layer projection of payment status with HTTP-friendly
# values. The canonical payment states are defined in core.domain.entities.payment_intent.PaymentStatus
# (PAYMENT_PENDING, PAID, REJECTED, EXPIRED, CANCELLED, REFUNDED).
# This HTTP-layer enum maps to a simplified view for API consumers.
class PaymentStatus(str, Enum):
    """Payment states for KR-033 flow (HTTP-layer projection)."""

    PENDING_RECEIPT = "PENDING_RECEIPT"
    PENDING_ADMIN_REVIEW = "PENDING_ADMIN_REVIEW"
    REJECTED = "REJECTED"
    PAID = "PAID"  # KR-033: set only after manual admin approval.


# NOTE: Matches core.domain.value_objects.qc_status.QCStatus exactly.
# Kept local to avoid pulling core dependency into HTTP layer.
class QCStatus(str, Enum):
    """KR-018 status values."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class CurrentUser(BaseModel):
    """Authenticated user projected from JWT middleware state."""

    model_config = ConfigDict(extra="ignore")

    user_id: str
    subject: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class RequestContext(BaseModel):
    """Request-scoped observability context."""

    model_config = ConfigDict(extra="ignore")

    corr_id: str | None = None
    client_ip_masked: str | None = None
    user_id: str | None = None


class RejectPaymentRequest(BaseModel):
    """Admin rejection payload."""

    reason: str = Field(min_length=3, max_length=500)


class PaymentIntentCreateRequest(BaseModel):
    """KR-081 contract stub; replace with contracts package model when available."""

    amount: float = Field(gt=0)
    season: str = Field(min_length=1, max_length=64)
    package_code: str = Field(min_length=1, max_length=64)
    field_ids: list[UUID] = Field(min_length=1)




class ReceiptUploadRequest(BaseModel):
    """Receipt upload payload (base64)."""

    filename: str = Field(min_length=1, max_length=256)
    content_type: str | None = Field(default=None, max_length=128)
    content_base64: str = Field(min_length=1)
class PaymentIntentResponse(BaseModel):
    """Payment intent read model."""

    intent_id: UUID
    status: PaymentStatus
    amount: float
    season: str
    package_code: str
    field_ids: list[UUID]
    created_at: datetime


class CalibrationRecordCreateRequest(BaseModel):
    """KR-081 contract stub for calibration record create."""

    drone_id: str = Field(min_length=1, max_length=128)
    field_id: UUID
    captured_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(min_length=1)


class CalibrationRecordResponse(BaseModel):
    """Calibration record read model."""

    record_id: UUID
    drone_id: str
    field_id: UUID
    captured_at: datetime
    metadata: dict[str, Any]
    evidence_refs: list[str]
    created_at: datetime


class QCReportCreateRequest(BaseModel):
    """KR-081 contract stub for QC report create."""

    calibration_record_id: UUID
    status: QCStatus
    checks: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)


class QCReportResponse(BaseModel):
    """QC report read model."""

    report_id: UUID
    calibration_record_id: UUID
    status: QCStatus
    checks: dict[str, Any]
    evidence_refs: list[str]
    created_at: datetime


class SLASummaryResponse(BaseModel):
    """SLA summary read model."""

    window_start: datetime
    window_end: datetime
    p95_latency_ms: float
    error_rate: float
    backlog: int


class SLABreachResponse(BaseModel):
    """SLA breach read model."""

    breach_id: UUID
    metric_name: str
    threshold: float
    observed_value: float
    started_at: datetime
    resolved_at: datetime | None = None


class AuditEvent(BaseModel):
    """Audit event payload (non-PII)."""

    event_type: str
    actor_user_id: str
    subject_id: str
    corr_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaymentService(Protocol):
    """Application-layer payment service port."""

    def create_intent(self, *, actor_user_id: str, payload: PaymentIntentCreateRequest, corr_id: str | None) -> PaymentIntentResponse:
        ...

    def upload_receipt(self, *, actor_user_id: str, intent_id: UUID, filename: str, content_type: str | None, content: bytes, corr_id: str | None) -> PaymentIntentResponse:
        ...

    def get_intent(self, *, actor_user_id: str, intent_id: UUID, corr_id: str | None) -> PaymentIntentResponse:
        ...

    def list_pending_payments(self, *, corr_id: str | None) -> list[PaymentIntentResponse]:
        ...

    def approve_payment(self, *, actor_user_id: str, payment_id: UUID, corr_id: str | None) -> PaymentIntentResponse:
        ...

    def reject_payment(self, *, actor_user_id: str, payment_id: UUID, reason: str, corr_id: str | None) -> PaymentIntentResponse:
        ...


class CalibrationService(Protocol):
    """Application-layer calibration service port."""

    def create_record(self, *, actor_user_id: str, payload: CalibrationRecordCreateRequest, corr_id: str | None) -> CalibrationRecordResponse:
        ...

    def get_record(self, *, record_id: UUID, corr_id: str | None) -> CalibrationRecordResponse | None:
        ...

    def list_records(
        self,
        *,
        corr_id: str | None,
        drone_id: str | None,
        field_id: UUID | None,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> list[CalibrationRecordResponse]:
        ...


class QCService(Protocol):
    """Application-layer QC service port."""

    def create_report(self, *, actor_user_id: str, payload: QCReportCreateRequest, corr_id: str | None) -> QCReportResponse:
        ...

    def get_report(self, *, report_id: UUID, corr_id: str | None) -> QCReportResponse | None:
        ...

    def list_reports(
        self,
        *,
        corr_id: str | None,
        calibration_record_id: UUID | None,
        status_filter: QCStatus | None,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> list[QCReportResponse]:
        ...


class SLAMetricsService(Protocol):
    """Application-layer SLA metrics service port."""

    def get_summary(self, *, start_at: datetime | None, end_at: datetime | None, corr_id: str | None) -> SLASummaryResponse:
        ...

    def list_breaches(self, *, start_at: datetime | None, end_at: datetime | None, corr_id: str | None) -> list[SLABreachResponse]:
        ...


class AuditPublisher(Protocol):
    """Audit sink port."""

    def publish(self, event: AuditEvent) -> None:
        ...


class MetricsCollector(Protocol):
    """Metrics sink port."""

    def observe_http(self, *, route: str, method: str, status_code: int, latency_ms: float, corr_id: str | None) -> None:
        ...

    def observe_status(self, *, route: str, status_code: int, corr_id: str | None) -> None:
        ...


@dataclass
class InMemoryAuditPublisher:
    """Fallback audit sink for local/dev use."""

    events: list[AuditEvent]

    def publish(self, event: AuditEvent) -> None:
        self.events.append(event)
        logger.info(
            "audit_event",
            extra={
                "event_type": event.event_type,
                "actor_user_id": event.actor_user_id,
                "subject_id": event.subject_id,
                "corr_id": event.corr_id,
            },
        )


class NoOpMetricsCollector:
    """Default collector when no metrics backend is bound."""

    def observe_http(self, *, route: str, method: str, status_code: int, latency_ms: float, corr_id: str | None) -> None:
        logger.debug(
            "http_observed",
            extra={
                "route": route,
                "method": method,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "corr_id": corr_id,
            },
        )

    def observe_status(self, *, route: str, status_code: int, corr_id: str | None) -> None:
        logger.debug(
            "status_observed",
            extra={"route": route, "status_code": status_code, "corr_id": corr_id},
        )


def _masked_client_ip(request: Request) -> str | None:
    client_host = request.client.host if request.client else None
    if not client_host:
        return None
    try:
        ip = ipaddress.ip_address(client_host)
    except ValueError:
        return None

    if ip.version == 4:
        network = ipaddress.ip_network(f"{ip}/24", strict=False)
    else:
        network = ipaddress.ip_network(f"{ip}/64", strict=False)
    return str(network.network_address)


def get_request_context(request: Request) -> RequestContext:
    """Return request metadata with masked IP and correlation id."""

    state_user = getattr(request.state, "user", None)
    user_id = state_user.get("user_id") if isinstance(state_user, dict) else None
    return RequestContext(
        corr_id=getattr(request.state, "corr_id", None),
        client_ip_masked=_masked_client_ip(request),
        user_id=user_id,
    )


def get_current_user(request: Request) -> CurrentUser:
    """Resolve authenticated principal from request state."""

    user_state = getattr(request.state, "user", None)
    if user_state is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # JWT middleware sets user as AuthenticatedUser dataclass; convert to dict for Pydantic
    if isinstance(user_state, dict):
        user_dict = user_state
    elif hasattr(user_state, "__dataclass_fields__"):
        from dataclasses import asdict
        user_dict = asdict(user_state)
    else:
        user_dict = {
            "user_id": getattr(user_state, "user_id", None) or getattr(user_state, "subject", None) or "",
            "subject": getattr(user_state, "subject", None),
            "roles": list(getattr(request.state, "roles", [])),
            "permissions": list(getattr(request.state, "permissions", [])),
        }

    user = CurrentUser.model_validate(user_dict)
    if not user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_roles(required_roles: list[str]) -> Callable[..., CurrentUser]:
    """Role-based guard dependency."""

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(required_roles).intersection(user.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


def require_permissions(required_permissions: list[str]) -> Callable[..., CurrentUser]:
    """Permission-based guard dependency."""

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(required_permissions).issubset(set(user.permissions)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


def get_payment_service(request: Request) -> PaymentService:
    service: PaymentService | None = getattr(request.app.state, "payment_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payment service unavailable")
    return service


def get_calibration_service(request: Request) -> CalibrationService:
    service: CalibrationService | None = getattr(request.app.state, "calibration_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Calibration service unavailable")
    return service


def get_qc_service(request: Request) -> QCService:
    service: QCService | None = getattr(request.app.state, "qc_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="QC service unavailable")
    return service


def get_sla_metrics_service(request: Request) -> SLAMetricsService:
    service: SLAMetricsService | None = getattr(request.app.state, "sla_metrics_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SLA metrics service unavailable")
    return service


def get_audit_publisher(request: Request) -> AuditPublisher:
    publisher: AuditPublisher | None = getattr(request.app.state, "audit_publisher", None)
    if publisher is None:
        sink: list[AuditEvent] = getattr(request.app.state, "audit_events", [])
        request.app.state.audit_events = sink
        return InMemoryAuditPublisher(events=sink)
    return publisher


def get_metrics_collector(request: Request) -> MetricsCollector:
    collector: MetricsCollector | None = getattr(request.app.state, "metrics_collector", None)
    if collector is None:
        return NoOpMetricsCollector()
    return collector


__all__ = [
    "AuditEvent",
    "AuditPublisher",
    "CalibrationRecordCreateRequest",
    "CalibrationRecordResponse",
    "CalibrationService",
    "CurrentUser",
    "MetricsCollector",
    "PaymentIntentCreateRequest",
    "PaymentIntentResponse",
    "PaymentService",
    "PaymentStatus",
    "QCReportCreateRequest",
    "QCReportResponse",
    "QCService",
    "QCStatus",
    "ReceiptUploadRequest",
    "RejectPaymentRequest",
    "RequestContext",
    "SLABreachResponse",
    "SLAMetricsService",
    "SLASummaryResponse",
    "get_audit_publisher",
    "get_calibration_service",
    "get_current_user",
    "get_metrics_collector",
    "get_payment_service",
    "get_qc_service",
    "get_request_context",
    "get_sla_metrics_service",
    "require_permissions",
    "require_roles",
]
