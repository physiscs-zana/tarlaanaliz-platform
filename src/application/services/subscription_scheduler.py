# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-015: Seasonal slot generation uses deterministic scheduling intervals.
# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Subscription sezonluk takvim üretimi ve mission zamanlama.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate'ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class SeasonPlan:
    subscription_id: str
    season_year: int
    mission_slots_ts_ms: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class UpcomingWindow:
    """KR-015-5: Otomatik sevk için sezonluk tarama penceresi."""

    slot_ts_ms: int
    window_start_ts_ms: int
    window_end_ts_ms: int


@dataclass(frozen=True, slots=True)
class SeasonPreviewDTO:
    """KR-015-5: Sezon takvimi önizlemesi (auto_dispatcher feed)."""

    subscription_id: str
    season_year: int
    upcoming_windows: tuple[UpcomingWindow, ...]


class SeasonSlotBuilder:
    """KR-015: Deterministik sezonluk slot üreticisi (port bağımlılığı yoktur).

    Sadece zaman damgası aralıklarını slot listesine çevirir.
    Port-bağımlı orkestrasyon için SubscriptionScheduler kullanılır.
    """

    def __init__(self, *, slot_interval_days: int = 14) -> None:
        self._interval_days = int(slot_interval_days)

    def build_season_plan(
        self,
        *,
        subscription_id: str,
        season_year: int,
        season_start_ts_ms: int,
        season_end_ts_ms: int,
        correlation_id: str,
    ) -> SeasonPlan:
        _ = correlation_id
        interval_ms = self._interval_days * 24 * 60 * 60 * 1000
        slots: list[int] = []
        cursor = int(season_start_ts_ms)
        while cursor <= int(season_end_ts_ms):
            slots.append(cursor)
            cursor += interval_ms
        return SeasonPlan(
            subscription_id=subscription_id,
            season_year=season_year,
            mission_slots_ts_ms=tuple(slots),
        )

    def get_upcoming_windows(
        self,
        season_plan: SeasonPlan,
        *,
        window_days: int = 3,
    ) -> SeasonPreviewDTO:
        """SeasonPlan slotlarını UpcomingWindow listesine dönüştürür (KR-015-5 auto_dispatcher feed).

        Args:
            season_plan: build_season_plan() çıktısı.
            window_days: Her slot için öncesi/sonrası gün sayısı (varsayılan 3).

        Returns:
            SeasonPreviewDTO: auto_dispatcher'a iletilecek pencere listesi.
        """
        window_ms = window_days * 24 * 60 * 60 * 1000
        windows = tuple(
            UpcomingWindow(
                slot_ts_ms=slot,
                window_start_ts_ms=slot - window_ms,
                window_end_ts_ms=slot + window_ms,
            )
            for slot in season_plan.mission_slots_ts_ms
        )
        return SeasonPreviewDTO(
            subscription_id=season_plan.subscription_id,
            season_year=season_plan.season_year,
            upcoming_windows=windows,
        )


class DomainServicePort(Protocol):
    def execute(self, *, command: dict[str, Any], correlation_id: str) -> dict[str, Any]: ...


class AuditLogPort(Protocol):
    def append(self, *, event_type: str, correlation_id: str, payload: dict[str, Any]) -> None: ...


@dataclass(slots=True)
class SubscriptionScheduler:
    """KR-027 / KR-015: Port-bağımlı abonelik zamanlama orkestratörü.

    SeasonSlotBuilder ile saf slot üretimi ayrıştırılmıştır; bu sınıf
    domain port'larını kullanarak komut yürütür ve audit log yazar.
    """

    domain_service: DomainServicePort
    audit_log: AuditLogPort

    def orchestrate(self, *, command: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        # KR-081: contract doğrulaması üst akışta tamamlanmış payload üzerinden çalışılır.
        result = self.domain_service.execute(command=command, correlation_id=correlation_id)
        self.audit_log.append(
            event_type="SubscriptionScheduler.orchestrate",
            correlation_id=correlation_id,
            payload={"status": result.get("status", "ok")},
        )
        return result

    @staticmethod
    def reschedule_next_due_at(
        subscription: Any,
        *,
        consume_token: bool = True,
        correlation_id: str = "",
    ) -> None:
        """KR-015-5: Abonelik next_due_at'ini reschedule eder.

        Args:
            subscription: Subscription domain entity'si.
            consume_token: True ise reschedule token tüketir (hava engeli gibi
                force-majeure durumlarında False geçirilir — KR-015-5).
            correlation_id: Gözlemlenebilirlik için korelasyon kimliği.
        """
        _ = correlation_id
        if consume_token:
            subscription.consume_reschedule_token()
        subscription.advance_due_date()
