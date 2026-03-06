# PATH: src/core/domain/value_objects/sla_metrics.py
# DESC: SLAMetrics VO; mission SLA metrikleri.
# SSOT: KR-015 (kapasite/planlama), KR-028 (mission lifecycle)
"""
SLAMetrics value object.

Mission bazlı SLA (Service Level Agreement) metriklerini temsil eder.
Planlama, uçuş, işleme ve teslimat aşamalarının süre ölçümlerini içerir.
KR-015 ve KR-028 ile tutarlı kalır.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, ClassVar, Optional


class SLAMetricsError(Exception):
    """SLAMetrics domain invariant ihlali."""


@dataclass(frozen=True)
class SLAMetrics:
    """Mission SLA metrikleri değer nesnesi.

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Ölçülen metrikler:
    - planned_at: Görev planlanma zamanı.
    - flight_started_at: Uçuş başlama zamanı.
    - flight_completed_at: Uçuş tamamlanma zamanı.
    - upload_completed_at: Veri yükleme tamamlanma zamanı.
    - analysis_completed_at: Analiz tamamlanma zamanı.
    - delivered_at: Sonuç teslim zamanı.

    Invariants:
    - planned_at zorunludur.
    - Zaman damgaları kronolojik sırada olmalıdır (varsa).
    """

    planned_at: datetime
    flight_started_at: Optional[datetime] = None
    flight_completed_at: Optional[datetime] = None
    upload_completed_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    # Varsayılan SLA limitleri (saat)
    DEFAULT_FLIGHT_SLA_HOURS: ClassVar[int] = 48
    DEFAULT_PROCESSING_SLA_HOURS: ClassVar[int] = 24
    DEFAULT_DELIVERY_SLA_HOURS: ClassVar[int] = 72

    def __post_init__(self) -> None:
        if self.planned_at is None:
            raise SLAMetricsError("planned_at zorunludur.")
        if not isinstance(self.planned_at, datetime):
            raise SLAMetricsError(f"planned_at datetime olmalıdır, alınan tip: {type(self.planned_at).__name__}")
        # Kronolojik sıra doğrulaması
        timestamps = [
            ("planned_at", self.planned_at),
            ("flight_started_at", self.flight_started_at),
            ("flight_completed_at", self.flight_completed_at),
            ("upload_completed_at", self.upload_completed_at),
            ("analysis_completed_at", self.analysis_completed_at),
            ("delivered_at", self.delivered_at),
        ]
        last_name: str | None = None
        last_ts: datetime | None = None
        for name, ts in timestamps:
            if ts is not None:
                if last_ts is not None and ts < last_ts:
                    raise SLAMetricsError(
                        f"Kronolojik sıra ihlali: {name} ({ts.isoformat()}) < {last_name} ({last_ts.isoformat()})"
                    )
                last_name = name
                last_ts = ts

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def flight_duration(self) -> Optional[timedelta]:
        """Uçuş süresi (başlangıç -> tamamlanma)."""
        if self.flight_started_at and self.flight_completed_at:
            return self.flight_completed_at - self.flight_started_at
        return None

    @property
    def processing_duration(self) -> Optional[timedelta]:
        """İşleme süresi (yükleme tamamlanma -> analiz tamamlanma)."""
        if self.upload_completed_at and self.analysis_completed_at:
            return self.analysis_completed_at - self.upload_completed_at
        return None

    @property
    def total_duration(self) -> Optional[timedelta]:
        """Toplam süre (planlama -> teslim)."""
        if self.delivered_at:
            return self.delivered_at - self.planned_at
        return None

    @property
    def wait_duration(self) -> Optional[timedelta]:
        """Bekleme süresi (planlama -> uçuş başlangıcı)."""
        if self.flight_started_at:
            return self.flight_started_at - self.planned_at
        return None

    @property
    def is_completed(self) -> bool:
        """Tüm aşamalar tamamlanmış mı?"""
        return self.delivered_at is not None

    def is_flight_sla_breached(
        self,
        sla_hours: int | None = None,
    ) -> bool:
        """Uçuş SLA'sı aşılmış mı?

        Planlama -> uçuş tamamlanma süresi kontrol edilir.
        """
        limit = sla_hours if sla_hours is not None else self.DEFAULT_FLIGHT_SLA_HOURS
        if self.flight_completed_at:
            elapsed = self.flight_completed_at - self.planned_at
            return elapsed > timedelta(hours=limit)
        return False

    def is_processing_sla_breached(
        self,
        sla_hours: int | None = None,
    ) -> bool:
        """İşleme SLA'sı aşılmış mı?"""
        limit = sla_hours if sla_hours is not None else self.DEFAULT_PROCESSING_SLA_HOURS
        duration = self.processing_duration
        if duration is not None:
            return duration > timedelta(hours=limit)
        return False

    def is_delivery_sla_breached(
        self,
        sla_hours: int | None = None,
    ) -> bool:
        """Toplam teslimat SLA'sı aşılmış mı?"""
        limit = sla_hours if sla_hours is not None else self.DEFAULT_DELIVERY_SLA_HOURS
        duration = self.total_duration
        if duration is not None:
            return duration > timedelta(hours=limit)
        return False

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""

        def _fmt(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() if dt else None

        return {
            "planned_at": self.planned_at.isoformat(),
            "flight_started_at": _fmt(self.flight_started_at),
            "flight_completed_at": _fmt(self.flight_completed_at),
            "upload_completed_at": _fmt(self.upload_completed_at),
            "analysis_completed_at": _fmt(self.analysis_completed_at),
            "delivered_at": _fmt(self.delivered_at),
            "is_completed": self.is_completed,
        }

    def __repr__(self) -> str:
        return f"SLAMetrics(planned_at='{self.planned_at.isoformat()}', is_completed={self.is_completed})"
