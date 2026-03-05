# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-071: Export orchestration emits outbound events only.
# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Training dataset export servisi.
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
etc.). The core EventBus is async/DomainEvent-based while these application-layer ports
use a simpler sync/string-based contract. An infrastructure adapter bridges between
these two abstractions at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


# Application-layer command DTO.
@dataclass(frozen=True, slots=True)
class TrainingExportRequest:
    export_id: str
    dataset_id: str
    format: str


# Application-layer port — NOT the same as core.ports.persistence.*Repository.
class TrainingExportStore(Protocol):
    def create_export_job(self, req: TrainingExportRequest) -> None: ...

    def mark_ready(self, export_id: str, *, uri: str) -> None: ...


# Application-layer port — sync/string-based, distinct from core.ports.messaging.EventBus
# (which is async/DomainEvent-based). Bridged via an infrastructure adapter.
class EventBus(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any], *, correlation_id: str) -> None: ...


class TrainingExportService:
    def __init__(self, store: TrainingExportStore, bus: EventBus) -> None:
        self._store = store
        self._bus = bus

    def request_export(self, *, req: TrainingExportRequest, correlation_id: str) -> None:
        self._store.create_export_job(req)
        self._bus.publish(
            "training_export.requested",
            {"export_id": req.export_id, "dataset_id": req.dataset_id, "format": req.format},
            correlation_id=correlation_id,
        )

    def mark_export_ready(self, *, export_id: str, uri: str, correlation_id: str) -> None:
        self._store.mark_ready(export_id, uri=uri)
        self._bus.publish(
            "training_export.ready",
            {"export_id": export_id, "uri": uri},
            correlation_id=correlation_id,
        )
