# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-081: Field CRUD orchestration uses explicit contract models and ports.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Field CRUD orkestrasyon servisi.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate’ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.

NOTE: The Protocol classes and dataclasses defined below are APPLICATION-LAYER ports
and DTOs, intentionally distinct from core domain types (core.ports.messaging.EventBus,
core.domain.entities.Field, etc.). The core EventBus is async/DomainEvent-based while
these application-layer ports use a simpler sync/string-based contract. An infrastructure
adapter bridges between these two abstractions at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


# Application-layer DTO — simplified projection of core.domain.entities.Field.
@dataclass(frozen=True, slots=True)
class Field:
    field_id: str
    owner_user_id: str
    name: str
    parcel_ref: str | None = None
    geometry_wkt: str | None = None


# Application-layer port — NOT the same as core.ports.persistence.*Repository.
class FieldRepository(Protocol):
    def create(self, field: Field) -> None: ...

    def get(self, field_id: str) -> Field | None: ...

    def update(self, field: Field) -> None: ...

    def delete(self, field_id: str) -> None: ...


# Application-layer port — sync/string-based, distinct from core.ports.messaging.EventBus
# (which is async/DomainEvent-based). Bridged via an infrastructure adapter.
class EventBus(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any], *, correlation_id: str) -> None: ...


class FieldService:
    def __init__(self, repo: FieldRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    def create_field(self, *, field: Field, correlation_id: str) -> None:
        self._repo.create(field)
        self._bus.publish(
            "field.created",
            {"field_id": field.field_id, "owner_user_id": field.owner_user_id},
            correlation_id=correlation_id,
        )

    def update_field(self, *, field: Field, correlation_id: str) -> None:
        self._repo.update(field)
        self._bus.publish("field.updated", {"field_id": field.field_id}, correlation_id=correlation_id)

    def delete_field(self, *, field_id: str, correlation_id: str) -> None:
        self._repo.delete(field_id)
        self._bus.publish("field.deleted", {"field_id": field_id}, correlation_id=correlation_id)
