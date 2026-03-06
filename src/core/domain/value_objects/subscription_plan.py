# PATH: src/core/domain/value_objects/subscription_plan.py
# DESC: SubscriptionPlan VO; abonelik plan detayları (immutable).
# SSOT: KR-015 (kapasite/planlama), KR-033 (ödeme akışı)
"""
SubscriptionPlan value object.

Abonelik planının temel parametrelerini immutable olarak temsil eder.
Plan tipi, analiz sayısı, tarama aralığı ve yeniden planlama hakkı gibi
sezonluk paket detaylarını içerir. KR-015-5 ile tutarlı kalır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class SubscriptionPlanError(Exception):
    """SubscriptionPlan domain invariant ihlali."""


@dataclass(frozen=True)
class SubscriptionPlan:
    """Abonelik planı değer nesnesi (KR-015, KR-033).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Plan tipleri:
    - BASIC: Temel paket (az analiz, kısa sezon).
    - STANDARD: Standart paket (orta düzey).
    - PREMIUM: Premium paket (çok analiz, uzun sezon).
    - CUSTOM: Özel paket (admin tarafından yapılandırılır).

    Invariants:
    - plan_code, tanımlı geçerli plan tiplerinden biri olmalıdır.
    - total_analyses > 0.
    - interval_days > 0.
    - reschedule_tokens >= 0.
    - price_kurus >= 0.
    """

    plan_code: str
    total_analyses: int
    interval_days: int
    reschedule_tokens: int
    price_kurus: int

    # Sabit plan kodları
    BASIC: ClassVar[str] = "BASIC"
    STANDARD: ClassVar[str] = "STANDARD"
    PREMIUM: ClassVar[str] = "PREMIUM"
    CUSTOM: ClassVar[str] = "CUSTOM"

    _VALID_CODES: ClassVar[frozenset[str]] = frozenset(
        {
            "BASIC",
            "STANDARD",
            "PREMIUM",
            "CUSTOM",
        }
    )

    # Plan -> Türkçe görünen ad eşlemesi
    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "BASIC": "Temel Paket",
        "STANDARD": "Standart Paket",
        "PREMIUM": "Premium Paket",
        "CUSTOM": "Özel Paket",
    }

    def __post_init__(self) -> None:
        if not isinstance(self.plan_code, str):
            raise SubscriptionPlanError(f"plan_code str olmalıdır, alınan tip: {type(self.plan_code).__name__}")
        normalized = self.plan_code.strip().upper()
        if normalized != self.plan_code:
            object.__setattr__(self, "plan_code", normalized)
        if self.plan_code not in self._VALID_CODES:
            raise SubscriptionPlanError(
                f"Geçersiz plan kodu: '{self.plan_code}'. Geçerli değerler: {sorted(self._VALID_CODES)}"
            )
        if not isinstance(self.total_analyses, int) or self.total_analyses <= 0:
            raise SubscriptionPlanError(f"total_analyses pozitif int olmalıdır, alınan: {self.total_analyses}")
        if not isinstance(self.interval_days, int) or self.interval_days <= 0:
            raise SubscriptionPlanError(f"interval_days pozitif int olmalıdır, alınan: {self.interval_days}")
        if not isinstance(self.reschedule_tokens, int) or self.reschedule_tokens < 0:
            raise SubscriptionPlanError(f"reschedule_tokens negatif olamaz, alınan: {self.reschedule_tokens}")
        if not isinstance(self.price_kurus, int) or self.price_kurus < 0:
            raise SubscriptionPlanError(f"price_kurus negatif olamaz, alınan: {self.price_kurus}")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Türkçe görünen ad."""
        return self._DISPLAY_NAMES[self.plan_code]

    @property
    def price_lira(self) -> float:
        """Fiyat TL cinsinden (görüntüleme için)."""
        return self.price_kurus / 100

    @property
    def estimated_season_days(self) -> int:
        """Tahmini sezon süresi (gün).

        (total_analyses - 1) * interval_days + 1
        """
        return (self.total_analyses - 1) * self.interval_days + 1

    @property
    def is_custom(self) -> bool:
        """Özel paket mi?"""
        return self.plan_code == self.CUSTOM

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------
    @classmethod
    def basic(cls, price_kurus: int) -> SubscriptionPlan:
        """Temel paket oluşturur: 4 analiz, 15 gün aralık, 1 reschedule."""
        return cls(
            plan_code=cls.BASIC,
            total_analyses=4,
            interval_days=15,
            reschedule_tokens=1,
            price_kurus=price_kurus,
        )

    @classmethod
    def standard(cls, price_kurus: int) -> SubscriptionPlan:
        """Standart paket oluşturur: 8 analiz, 10 gün aralık, 2 reschedule."""
        return cls(
            plan_code=cls.STANDARD,
            total_analyses=8,
            interval_days=10,
            reschedule_tokens=2,
            price_kurus=price_kurus,
        )

    @classmethod
    def premium(cls, price_kurus: int) -> SubscriptionPlan:
        """Premium paket oluşturur: 12 analiz, 7 gün aralık, 3 reschedule."""
        return cls(
            plan_code=cls.PREMIUM,
            total_analyses=12,
            interval_days=7,
            reschedule_tokens=3,
            price_kurus=price_kurus,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "plan_code": self.plan_code,
            "display_name": self.display_name,
            "total_analyses": self.total_analyses,
            "interval_days": self.interval_days,
            "reschedule_tokens": self.reschedule_tokens,
            "price_kurus": self.price_kurus,
            "price_lira": self.price_lira,
            "estimated_season_days": self.estimated_season_days,
        }

    def __str__(self) -> str:
        return self.plan_code

    def __repr__(self) -> str:
        return (
            f"SubscriptionPlan(plan_code='{self.plan_code}', "
            f"analyses={self.total_analyses}, "
            f"interval={self.interval_days}d, "
            f"price={self.price_lira:.2f}TL)"
        )
