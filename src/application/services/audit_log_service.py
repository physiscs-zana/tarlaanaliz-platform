# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-033: Audit actions are emitted and persisted by a single application service.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    SCHEDULE = "schedule"
    START = "start"
    COMPLETE = "complete"
    EXPORT = "export"


@dataclass(frozen=True, slots=True)
class Actor:
    actor_id: str
    roles: tuple[str, ...] = ()
    tenant_id: str | None = None


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    ts_ms: int
    correlation_id: str
    actor: Actor
    action: AuditAction
    resource_type: str
    resource_id: str
    outcome: str
    meta: dict[str, Any] = field(default_factory=dict)


class AuditLogRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...


class Clock(Protocol):
    def now_ms(self) -> int: ...


class SystemClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)


class AuditLogService:
    def __init__(self, repo: AuditLogRepository, clock: Clock | None = None) -> None:
        self._repo = repo
        self._clock = clock or SystemClock()

    def emit(
        self,
        *,
        correlation_id: str,
        actor: Actor,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        outcome: str,
        meta: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            ts_ms=self._clock.now_ms(),
            correlation_id=correlation_id,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            meta=meta or {},
        )
        self._repo.append(event)
        return event
