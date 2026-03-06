# PATH: src/core/domain/value_objects/crop_ops_profile.py
# DESC: CropOpsProfile VO; bitki bazlı operasyonel parametreler.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from src.core.domain.value_objects.crop_type import CropType


class CropOpsProfileError(Exception):
    """CropOpsProfile domain invariant ihlali."""


@dataclass(frozen=True)
class CropOpsProfile:
    """Bitki bazlı operasyonel kapasite profili (KR-015-1).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Admin tarafından her CropType için tanımlanır:
    - daily_capacity_donum: Günlük kapasite (dönüm). Varsayılan: 2750, önerilen: 2500-3000.
    - system_seed_quota: SYSTEM_SEED_QUOTA (dönüm). Varsayılan: 1500.
    - pull_quota: Çiftçi seçimi / pilot kaynaklı iş kotası.
      Hesaplama: daily_capacity_donum - system_seed_quota
    - overage_tolerance: Kapasite aşım toleransı (varsayılan: %10 = 0.10).

    KR-015-2: Günlük kapasite ikiye ayrılır:
    - SYSTEM_SEED_QUOTA: Sistem tarafından atanan, reddedilemez görevler.
    - PULL_QUOTA: Kalan kapasite (çiftçi seçimi veya pilot kaynaklı).

    Invariants:
    - crop_type geçerli bir CropType olmalıdır.
    - daily_capacity_donum, MIN_CAPACITY ile MAX_CAPACITY arasında olmalıdır.
    - system_seed_quota, 0 ile daily_capacity_donum arasında olmalıdır.
    - overage_tolerance, 0.0-1.0 arasında olmalıdır.
    """

    crop_type: CropType
    daily_capacity_donum: int
    system_seed_quota: int
    overage_tolerance: float

    DEFAULT_CAPACITY: ClassVar[int] = 2750
    MIN_CAPACITY: ClassVar[int] = 2500
    MAX_CAPACITY: ClassVar[int] = 3000
    DEFAULT_SEED_QUOTA: ClassVar[int] = 1500
    DEFAULT_OVERAGE_TOLERANCE: ClassVar[float] = 0.10

    def __post_init__(self) -> None:
        if not isinstance(self.crop_type, CropType):
            raise CropOpsProfileError(f"crop_type CropType olmalıdır, alınan tip: {type(self.crop_type).__name__}")
        if not isinstance(self.daily_capacity_donum, int):
            raise CropOpsProfileError(
                f"daily_capacity_donum int olmalıdır, alınan tip: {type(self.daily_capacity_donum).__name__}"
            )
        if not (self.MIN_CAPACITY <= self.daily_capacity_donum <= self.MAX_CAPACITY):
            raise CropOpsProfileError(
                f"daily_capacity_donum {self.MIN_CAPACITY}-{self.MAX_CAPACITY} arasında olmalıdır, "
                f"alınan: {self.daily_capacity_donum}"
            )
        if not isinstance(self.system_seed_quota, int):
            raise CropOpsProfileError(
                f"system_seed_quota int olmalıdır, alınan tip: {type(self.system_seed_quota).__name__}"
            )
        if not (0 <= self.system_seed_quota <= self.daily_capacity_donum):
            raise CropOpsProfileError(
                f"system_seed_quota 0 ile daily_capacity_donum({self.daily_capacity_donum}) "
                f"arasında olmalıdır, alınan: {self.system_seed_quota}"
            )
        if not isinstance(self.overage_tolerance, (int, float)):
            raise CropOpsProfileError(
                f"overage_tolerance sayısal olmalıdır, alınan tip: {type(self.overage_tolerance).__name__}"
            )
        if isinstance(self.overage_tolerance, int):
            object.__setattr__(self, "overage_tolerance", float(self.overage_tolerance))
        if not (0.0 <= self.overage_tolerance <= 1.0):
            raise CropOpsProfileError(f"overage_tolerance 0.0-1.0 arasında olmalıdır, alınan: {self.overage_tolerance}")

    @classmethod
    def create_default(cls, crop_type: CropType) -> CropOpsProfile:
        """Varsayılan profil oluşturur (KR-015-1).

        Varsayılanlar: daily_capacity=2750, seed_quota=1500, overage=%10.
        """
        return cls(
            crop_type=crop_type,
            daily_capacity_donum=cls.DEFAULT_CAPACITY,
            system_seed_quota=cls.DEFAULT_SEED_QUOTA,
            overage_tolerance=cls.DEFAULT_OVERAGE_TOLERANCE,
        )

    @property
    def pull_quota(self) -> int:
        """PULL_QUOTA: Çiftçi seçimi / pilot kaynaklı iş kotası (KR-015-2)."""
        return self.daily_capacity_donum - self.system_seed_quota

    @property
    def max_capacity_with_overage(self) -> int:
        """Acil durum kapasite aşımı dahil maksimum (KR-015-1).

        daily_capacity_donum * (1 + overage_tolerance)
        """
        return int(self.daily_capacity_donum * (1.0 + self.overage_tolerance))

    def can_accept_mission(self, current_load_donum: int, mission_area_donum: int) -> bool:
        """Mevcut yük + yeni görev, kapasite dahilinde mi?

        Acil durum toleransı dahil kontrol eder.
        """
        return (current_load_donum + mission_area_donum) <= self.max_capacity_with_overage

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "crop_type": self.crop_type.to_dict(),
            "daily_capacity_donum": self.daily_capacity_donum,
            "system_seed_quota": self.system_seed_quota,
            "pull_quota": self.pull_quota,
            "overage_tolerance": self.overage_tolerance,
            "max_capacity_with_overage": self.max_capacity_with_overage,
        }

    def __repr__(self) -> str:
        return (
            f"CropOpsProfile(crop_type='{self.crop_type.code}', "
            f"capacity={self.daily_capacity_donum}, "
            f"seed_quota={self.system_seed_quota}, "
            f"pull_quota={self.pull_quota})"
        )
