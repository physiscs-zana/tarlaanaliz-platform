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
class CreateFieldCommand:
    owner_id: str
    name: str
    parcel_ref: str
    geometry: dict[str, Any]
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class CreateFieldResult:
    field_id: str
    owner_id: str
    name: str
    correlation_id: str


class FieldServicePort(Protocol):
    def create_field(
        self,
        *,
        owner_id: str,
        name: str,
        parcel_ref: str,
        geometry: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class CreateFieldDeps(Protocol):
    field_service: FieldServicePort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def handle(command: CreateFieldCommand, *, ctx: RequestContext, deps: CreateFieldDeps) -> CreateFieldResult:
    if not {"admin", "ops", "farmer"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    if not command.name.strip():
        raise ValueError("field_name_required")

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return CreateFieldResult(
                field_id=str(cached["field_id"]),
                owner_id=str(cached["owner_id"]),
                name=str(cached["name"]),
                correlation_id=ctx.correlation_id,
            )

    created = deps.field_service.create_field(
        owner_id=command.owner_id,
        name=command.name,
        parcel_ref=command.parcel_ref,
        geometry=command.geometry,
        correlation_id=ctx.correlation_id,
    )

    field_id = str(created.get("field_id", ""))
    if not field_id:
        raise RuntimeError("field_create_failed")

    deps.audit_log.log(
        action="create_field",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"field_id": field_id, "owner_id": command.owner_id, "error_code": None},
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key,
            value={"field_id": field_id, "owner_id": command.owner_id, "name": command.name},
        )

    return CreateFieldResult(
        field_id=field_id,
        owner_id=command.owner_id,
        name=command.name,
        correlation_id=ctx.correlation_id,
    )
