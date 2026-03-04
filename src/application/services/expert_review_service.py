# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-081: Expert review orchestration consumes explicit contracts.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Expert review orkestrasyon servisi.
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


# Application-layer DTO — simplified projection for use-case orchestration.
@dataclass(frozen=True, slots=True)
class ExpertReview:
    review_id: str
    analysis_id: str
    expert_id: str
    status: str
    notes: str | None = None


# Application-layer port — NOT the same as core.ports.persistence.*Repository.
class ExpertReviewRepository(Protocol):
    def create(self, review: ExpertReview) -> None: ...

    def get(self, review_id: str) -> ExpertReview | None: ...

    def list_pending(self, *, limit: int) -> tuple[ExpertReview, ...]: ...

    def update(self, review: ExpertReview) -> None: ...


# Application-layer port — sync/string-based, distinct from core.ports.messaging.EventBus
# (which is async/DomainEvent-based). Bridged via an infrastructure adapter.
class EventBus(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any], *, correlation_id: str) -> None: ...


class ExpertReviewService:
    def __init__(self, repo: ExpertReviewRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    def create_review(self, *, review: ExpertReview, correlation_id: str) -> None:
        self._repo.create(review)
        self._bus.publish(
            "expert_review.created",
            {"review_id": review.review_id, "analysis_id": review.analysis_id, "expert_id": review.expert_id},
            correlation_id=correlation_id,
        )

    def submit_review(self, *, review_id: str, notes: str, correlation_id: str) -> ExpertReview:
        review = self._repo.get(review_id)
        if review is None:
            raise ValueError("expert review not found")
        updated = ExpertReview(
            review_id=review.review_id,
            analysis_id=review.analysis_id,
            expert_id=review.expert_id,
            status="completed",
            notes=notes,
        )
        self._repo.update(updated)
        self._bus.publish(
            "expert_review.completed",
            {"review_id": updated.review_id, "analysis_id": updated.analysis_id, "expert_id": updated.expert_id},
            correlation_id=correlation_id,
        )
        return updated
