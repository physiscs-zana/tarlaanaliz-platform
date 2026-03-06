# PATH: src/core/domain/value_objects/sla_threshold.py
# DESC: SLAThreshold VO; servis seviyesi eşikleri.
# SSOT: KR-015 (kapasite/planlama), KR-028 (mission lifecycle)
"""
SLAThreshold value object.

Servis seviyesi anlaşması (SLA) eşik değerlerini temsil eder.
Her aşama için saat cinsinden hedef ve maksimum süre limitleri tanımlar.
SLAMetrics ile birlikte kullanılarak ihlal kontrolü yapılır.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, ClassVar


class SLAThresholdError(Exception):
    """SLAThreshold domain invariant ihlali."""


@dataclass(frozen=True)
class SLAThreshold:
    """SLA eşik değeri değer nesnesi.

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Her eşik iki limit içerir:
    - target_hours: Hedef süre (ideal tamamlanma süresi).
    - max_hours: Maksimum süre (bu süre aşılırsa SLA ihlali oluşur).

    Invariants:
    - target_hours > 0.
    - max_hours >= target_hours.
    """

    target_hours: float
    max_hours: float

    # Varsayılan eşikler (saat cinsinden)
    DEFAULT_FLIGHT_TARGET: ClassVar[float] = 24.0
    DEFAULT_FLIGHT_MAX: ClassVar[float] = 48.0
    DEFAULT_PROCESSING_TARGET: ClassVar[float] = 12.0
    DEFAULT_PROCESSING_MAX: ClassVar[float] = 24.0
    DEFAULT_DELIVERY_TARGET: ClassVar[float] = 48.0
    DEFAULT_DELIVERY_MAX: ClassVar[float] = 72.0

    def __post_init__(self) -> None:
        if not isinstance(self.target_hours, (int, float)):
            raise SLAThresholdError(f"target_hours sayısal olmalıdır, alınan tip: {type(self.target_hours).__name__}")
        if not isinstance(self.max_hours, (int, float)):
            raise SLAThresholdError(f"max_hours sayısal olmalıdır, alınan tip: {type(self.max_hours).__name__}")
        # int -> float dönüşümü
        if isinstance(self.target_hours, int):
            object.__setattr__(self, "target_hours", float(self.target_hours))
        if isinstance(self.max_hours, int):
            object.__setattr__(self, "max_hours", float(self.max_hours))
        if self.target_hours <= 0:
            raise SLAThresholdError(f"target_hours 0'dan büyük olmalıdır, alınan: {self.target_hours}")
        if self.max_hours < self.target_hours:
            raise SLAThresholdError(
                f"max_hours ({self.max_hours}) target_hours ({self.target_hours}) değerinden küçük olamaz."
            )

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def target_timedelta(self) -> timedelta:
        """Hedef süre timedelta olarak."""
        return timedelta(hours=self.target_hours)

    @property
    def max_timedelta(self) -> timedelta:
        """Maksimum süre timedelta olarak."""
        return timedelta(hours=self.max_hours)

    def is_within_target(self, elapsed: timedelta) -> bool:
        """Geçen süre hedef içinde mi?"""
        return elapsed <= self.target_timedelta

    def is_breached(self, elapsed: timedelta) -> bool:
        """SLA ihlal edilmiş mi? (max_hours aşılmış mı?)"""
        return elapsed > self.max_timedelta

    def is_at_risk(self, elapsed: timedelta) -> bool:
        """SLA risk altında mı? (hedef aşılmış ama max aşılmamış)."""
        return not self.is_within_target(elapsed) and not self.is_breached(elapsed)

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------
    @classmethod
    def flight_default(cls) -> SLAThreshold:
        """Uçuş aşaması için varsayılan SLA eşiği."""
        return cls(
            target_hours=cls.DEFAULT_FLIGHT_TARGET,
            max_hours=cls.DEFAULT_FLIGHT_MAX,
        )

    @classmethod
    def processing_default(cls) -> SLAThreshold:
        """İşleme aşaması için varsayılan SLA eşiği."""
        return cls(
            target_hours=cls.DEFAULT_PROCESSING_TARGET,
            max_hours=cls.DEFAULT_PROCESSING_MAX,
        )

    @classmethod
    def delivery_default(cls) -> SLAThreshold:
        """Teslimat aşaması için varsayılan SLA eşiği."""
        return cls(
            target_hours=cls.DEFAULT_DELIVERY_TARGET,
            max_hours=cls.DEFAULT_DELIVERY_MAX,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "target_hours": self.target_hours,
            "max_hours": self.max_hours,
        }

    def __repr__(self) -> str:
        return f"SLAThreshold(target_hours={self.target_hours}, max_hours={self.max_hours})"
