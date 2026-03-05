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
class ReportWeatherBlockCommand:
    mission_id: str
    reason_code: str
    details: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ReportWeatherBlockResult:
    weather_block_id: str
    status: str
    correlation_id: str


class WeatherBlockServicePort(Protocol):
    def report_block(
        self,
        *,
        mission_id: str,
        pilot_id: str,
        reason_code: str,
        details: str | None,
        correlation_id: str,
    ) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def log(self, *, action: str, correlation_id: str, actor_id: str, payload: dict[str, Any]) -> None: ...


class IdempotencyPort(Protocol):
    def get(self, *, key: str) -> dict[str, Any] | None: ...

    def set(self, *, key: str, value: dict[str, Any]) -> None: ...


class ReportWeatherBlockDeps(Protocol):
    weather_block_service: WeatherBlockServicePort
    audit_log: AuditLogPort
    idempotency: IdempotencyPort | None


def handle(
    command: ReportWeatherBlockCommand, *, ctx: RequestContext, deps: ReportWeatherBlockDeps
) -> ReportWeatherBlockResult:
    if not {"pilot", "admin", "ops"}.intersection(ctx.roles):
        raise PermissionError("forbidden")

    if command.idempotency_key and deps.idempotency is not None:
        cached = deps.idempotency.get(key=command.idempotency_key)
        if cached is not None:
            return ReportWeatherBlockResult(
                weather_block_id=str(cached["weather_block_id"]),
                status=str(cached["status"]),
                correlation_id=ctx.correlation_id,
            )

    report = deps.weather_block_service.report_block(
        mission_id=command.mission_id,
        pilot_id=ctx.actor_id,
        reason_code=command.reason_code,
        details=command.details,
        correlation_id=ctx.correlation_id,
    )

    weather_block_id = str(report.get("weather_block_id", ""))
    if not weather_block_id:
        raise RuntimeError("weather_block_report_failed")

    deps.audit_log.log(
        action="report_weather_block",
        correlation_id=ctx.correlation_id,
        actor_id=ctx.actor_id,
        payload={"weather_block_id": weather_block_id, "mission_id": command.mission_id, "error_code": None},
    )

    if command.idempotency_key and deps.idempotency is not None:
        deps.idempotency.set(
            key=command.idempotency_key, value={"weather_block_id": weather_block_id, "status": "reported"}
        )

    return ReportWeatherBlockResult(
        weather_block_id=weather_block_id, status="reported", correlation_id=ctx.correlation_id
    )
