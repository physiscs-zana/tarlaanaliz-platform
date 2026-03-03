# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-015: Weekly windows are generated from deterministic slot-per-day rules.
# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Haftalık görev penceresi hesaplama.
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
class WeeklyWindow:
    week_start_ts_ms: int
    week_end_ts_ms: int
    slots_ts_ms: tuple[int, ...]


class WeeklyWindowScheduler:
    def __init__(self, *, slot_per_day: int = 1) -> None:
        self._slot_per_day = max(1, int(slot_per_day))

    def build_week(self, *, week_start_ts_ms: int, correlation_id: str) -> WeeklyWindow:
        _ = correlation_id
        day_ms = 24 * 60 * 60 * 1000
        week_end = int(week_start_ts_ms) + (7 * day_ms) - 1
        slots: list[int] = []
        for day_index in range(7):
            day_start = int(week_start_ts_ms) + (day_index * day_ms)
            for slot_index in range(self._slot_per_day):
                slots.append(day_start + (slot_index * (day_ms // self._slot_per_day)))
        return WeeklyWindow(week_start_ts_ms=int(week_start_ts_ms), week_end_ts_ms=week_end, slots_ts_ms=tuple(slots))
