# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/ports/repositories/dataset_repository.py
# DESC: DatasetRepository port; KR-072 dataset durum yönetimi.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-072 (Dataset durum makinesi)
"""
DatasetRepository port (Protocol).

KR-072: Dataset'in 9+1 durum makinesi boyunca kalıcılığını sağlar.
Implementation: src/infrastructure/persistence/sqlalchemy/repositories/dataset_repository_impl.py
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from src.core.domain.entities.dataset import Dataset
from src.core.domain.value_objects.dataset_status import DatasetStatus


@runtime_checkable
class DatasetRepository(Protocol):
    """Dataset kalıcılık portu (KR-072).

    Tüm metodlar async; SQLAlchemy async session veya diğer storage
    backend'leri bu Protocol'u implement eder.
    """

    async def save(self, dataset: Dataset) -> None:
        """Yeni dataset kaydı oluştur veya güncelle."""
        ...

    async def get_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """Dataset ID ile getir. Bulunamazsa None döner."""
        ...

    async def get_by_mission_id(self, mission_id: UUID) -> list[Dataset]:
        """Bir mission'a ait tüm dataset'leri getir."""
        ...

    async def get_by_status(
        self,
        status: DatasetStatus,
        *,
        province_code: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dataset]:
        """Verilen durumdaki dataset'leri getir.

        Args:
            status: Filtrelenecek durum.
            province_code: İl filtresi (IL_OPERATOR KR-083 görüntüleme kısıtı).
            limit: Maksimum kayıt sayısı.
        """
        ...

    async def get_quarantined(
        self,
        *,
        province_code: Optional[str] = None,
        limit: int = 50,
    ) -> list[Dataset]:
        """REJECTED_QUARANTINE durumundaki dataset'leri getir.

        KR-041: Quarantine queue monitoring zorunlu.
        """
        ...

    async def update_status(
        self,
        dataset_id: UUID,
        new_status: DatasetStatus,
    ) -> None:
        """Sadece status alanını güncelle (optimistik locking önerilir)."""
        ...

    async def count_by_status(self, status: DatasetStatus) -> int:
        """Verilen durumdaki dataset sayısını döner (SLA/monitoring)."""
        ...
