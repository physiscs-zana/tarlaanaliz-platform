# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: Command contracts are defined before orchestration logic.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RequestContext:
    actor_id: str
    roles: tuple[str, ...]
    correlation_id: str


@dataclass(frozen=True, slots=True)
class RegisterExpertCommand:
    display_name: str
    phone_number: str
    region_code: str
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterExpertResult:
    expert_id: str
    display_name: str
    correlation_id: str


class ExpertServicePort(Protocol):
    def register_expert(
        self,
        *,
        display_name: str,
        phone_number: str,
        region_code: str,
        correlation_id: str,
    ) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class RegisterExpertDeps(Protocol):
    expert_service: ExpertServicePort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def handle(command: RegisterExpertCommand, *, ctx: RequestContext, deps: RegisterExpertDeps) -> RegisterExpertResult:
    if "admin" not in ctx.roles:
        raise PermissionError("forbidden")

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return RegisterExpertResult(
                expert_id=str(cached["expert_id"]),
                display_name=str(cached["display_name"]),
                correlation_id=ctx.correlation_id,
            )

    created = deps.expert_service.register_expert(
        display_name=command.display_name,
        phone_number=command.phone_number,
        region_code=command.region_code,
        correlation_id=ctx.correlation_id,
    )

    expert_id = str(created.get("expert_id", ""))
    if not expert_id:
        raise RuntimeError("expert_register_failed")

    deps.audit_log.log(
        action="register_expert",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={
            "expert_id": expert_id,
            # PII minimal: phone number saklanmaz.
            "region_code": command.region_code,
            "error_code": None,
        },
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key, value={"expert_id": expert_id, "display_name": command.display_name}
        )

    return RegisterExpertResult(
        expert_id=expert_id, display_name=command.display_name, correlation_id=ctx.correlation_id
    )
