# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-015: Capacity policy and estimations are centralized for scheduling inputs.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: "dönüm → efor → kapasite" hesaplarını standardize etmek.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate’ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanningCapacityPolicy:
    min_daily_capacity_donum: int = 2500
    max_daily_capacity_donum: int = 3000
    work_days_max: int = 6
    effort_per_donum: float = 1.0


@dataclass(frozen=True, slots=True)
class CapacityEstimate:
    donum: float
    effort_units: float
    daily_capacity_donum: int
    estimated_days: float


def donum_to_effort(donum: float, *, policy: PlanningCapacityPolicy | None = None) -> float:
    p = policy or PlanningCapacityPolicy()
    return max(0.0, float(donum)) * p.effort_per_donum


def estimate_daily_capacity(*, requested: int, policy: PlanningCapacityPolicy | None = None) -> int:
    p = policy or PlanningCapacityPolicy()
    return max(p.min_daily_capacity_donum, min(p.max_daily_capacity_donum, int(requested)))


def estimate_days_for_area(
    donum: float,
    *,
    daily_capacity_donum: int,
    policy: PlanningCapacityPolicy | None = None,
) -> float:
    capacity = estimate_daily_capacity(requested=daily_capacity_donum, policy=policy)
    if capacity <= 0:
        return float("inf")
    return float(donum) / float(capacity)


def estimate_capacity(
    donum: float,
    *,
    daily_capacity_donum: int,
    policy: PlanningCapacityPolicy | None = None,
) -> CapacityEstimate:
    effort = donum_to_effort(donum, policy=policy)
    capacity = estimate_daily_capacity(requested=daily_capacity_donum, policy=policy)
    days = estimate_days_for_area(donum, daily_capacity_donum=capacity, policy=policy)
    return CapacityEstimate(donum=float(donum), effort_units=effort, daily_capacity_donum=capacity, estimated_days=days)
class CapacityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    area_donum: float
    effort_points: float
    required_pilots: int


@dataclass(slots=True)
class PlanningCapacityService:
    effort_per_donum: float = 1.0
    max_daily_effort_per_pilot: float = 200.0

    def calculate(self, *, area_donum: float) -> CapacityPlan:
        if area_donum <= 0:
            raise CapacityError("area_donum_must_be_positive")

        effort_points = area_donum * self.effort_per_donum
        required_pilots = max(1, int(-(-effort_points // self.max_daily_effort_per_pilot)))

        # KR-015: kapasite planlaması kontrollü hesap ile standardize edilir.
        return CapacityPlan(
            area_donum=area_donum,
            effort_points=effort_points,
            required_pilots=required_pilots,
        )
