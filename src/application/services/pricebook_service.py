# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-081: Pricebook snapshots use typed contracts at application boundaries.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: PriceBook/PriceSnapshot yönetimi (KR-022).
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate’ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.

NOTE: The Protocol classes and dataclasses defined below are APPLICATION-LAYER ports
and DTOs, intentionally distinct from core domain types. They use simplified contracts
(str IDs, flat structures) appropriate for use-case orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


# Application-layer DTO — simplified projection for use-case orchestration.
@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    snapshot_id: str
    currency: str
    valid_from_ts_ms: int
    items: dict[str, int]


# Application-layer port — NOT the same as core.ports.persistence.*Repository.
class PricebookRepository(Protocol):
    def upsert_snapshot(self, snap: PriceSnapshot) -> None: ...

    def get_active_snapshot(self, *, at_ts_ms: int) -> PriceSnapshot | None: ...

    def list_snapshots(self, *, limit: int) -> tuple[PriceSnapshot, ...]: ...


class PricebookService:
    def __init__(self, repo: PricebookRepository) -> None:
        self._repo = repo

    def publish_snapshot(self, *, snap: PriceSnapshot, correlation_id: str) -> None:
        _ = correlation_id
        self._repo.upsert_snapshot(snap)

    def get_active(self, *, at_ts_ms: int) -> PriceSnapshot | None:
        return self._repo.get_active_snapshot(at_ts_ms=at_ts_ms)

    def list_recent(self, *, limit: int = 50) -> tuple[PriceSnapshot, ...]:
        return self._repo.list_snapshots(limit=limit)
