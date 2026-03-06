# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/ports/repositories/crop_ops_profile_repository.py
# DESC: CropOpsProfileRepository port; KR-015-1 bitki bazlı operasyonel profil kalıcılığı.
"""
CropOpsProfileRepository port (Protocol).

KR-015-1: Bitki bazlı operasyonel kapasite profillerinin kalıcılığını sağlar.
Implementation: src/infrastructure/persistence/sqlalchemy/repositories/crop_ops_profile_repository_impl.py
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from src.core.domain.value_objects.crop_ops_profile import CropOpsProfile
from src.core.domain.value_objects.crop_type import CropType


@runtime_checkable
class CropOpsProfileRepository(Protocol):
    """CropOpsProfile kalıcılık portu (KR-015-1).

    Tüm metodlar async; SQLAlchemy async session veya diğer storage
    backend'leri bu Protocol'u implement eder.
    """

    async def save(self, profile: CropOpsProfile) -> None:
        """Profil kaydı oluştur veya güncelle."""
        ...

    async def get_by_crop_type(self, crop_type: CropType) -> Optional[CropOpsProfile]:
        """Bitki türüne göre profil getir. Bulunamazsa None döner."""
        ...

    async def get_all(self) -> list[CropOpsProfile]:
        """Tüm profilleri getir."""
        ...

    async def delete(self, crop_type: CropType) -> None:
        """Bitki türüne göre profili sil."""
        ...
