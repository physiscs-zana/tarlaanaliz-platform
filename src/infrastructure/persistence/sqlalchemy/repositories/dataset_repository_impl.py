# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/infrastructure/persistence/sqlalchemy/repositories/dataset_repository_impl.py
# DESC: DatasetRepository portunun SQLAlchemy implementasyonu; KR-072 dataset durum yönetimi.
"""
DatasetRepository SQLAlchemy implementasyonu.

KR-072: Dataset'in 9+1 durum makinesi boyunca kalıcılığını sağlar.
Port: src/core/ports/repositories/dataset_repository.py
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.entities.dataset import Dataset
from src.core.domain.value_objects.dataset_status import DatasetStatus
from src.infrastructure.persistence.sqlalchemy.models.dataset_model import DatasetModel

logger = structlog.get_logger(__name__)


class DatasetRepositoryImpl:
    """DatasetRepository portunun SQLAlchemy async implementasyonu (KR-072)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: DatasetModel) -> Dataset:
        """ORM modelini domain entity'sine donusturur."""
        return Dataset(
            dataset_id=model.dataset_id,
            mission_id=model.mission_id,
            field_id=model.field_id,
            status=DatasetStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            sha256_hash=model.sha256_hash,
            manifest=model.manifest,
            av1_report_uri=model.av1_report_uri,
            av2_report_uri=model.av2_report_uri,
            is_calibrated=model.is_calibrated,
            worker_job_id=model.worker_job_id,
            result_uri=model.result_uri,
            signature=model.signature,
            quarantine_reason=model.quarantine_reason,
            available_bands=tuple(model.available_bands) if model.available_bands else (),
        )

    def _to_model(self, entity: Dataset) -> DatasetModel:
        """Domain entity'sini ORM modeline donusturur."""
        return DatasetModel(
            dataset_id=entity.dataset_id,
            mission_id=entity.mission_id,
            field_id=entity.field_id,
            status=entity.status.value,
            sha256_hash=entity.sha256_hash,
            manifest=entity.manifest,
            av1_report_uri=entity.av1_report_uri,
            av2_report_uri=entity.av2_report_uri,
            is_calibrated=entity.is_calibrated,
            worker_job_id=entity.worker_job_id,
            result_uri=entity.result_uri,
            signature=entity.signature,
            quarantine_reason=entity.quarantine_reason,
            available_bands=list(entity.available_bands),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------

    async def save(self, dataset: Dataset) -> None:
        """Yeni dataset kaydı oluştur veya güncelle."""
        existing = await self._session.get(DatasetModel, dataset.dataset_id)
        if existing:
            existing.status = dataset.status.value
            existing.sha256_hash = dataset.sha256_hash
            existing.manifest = dataset.manifest
            existing.av1_report_uri = dataset.av1_report_uri
            existing.av2_report_uri = dataset.av2_report_uri
            existing.is_calibrated = dataset.is_calibrated
            existing.worker_job_id = dataset.worker_job_id
            existing.result_uri = dataset.result_uri
            existing.signature = dataset.signature
            existing.quarantine_reason = dataset.quarantine_reason
            existing.available_bands = list(dataset.available_bands)
            existing.updated_at = dataset.updated_at
        else:
            self._session.add(self._to_model(dataset))
        await self._session.flush()
        logger.info(
            "dataset_saved",
            dataset_id=str(dataset.dataset_id),
            status=dataset.status.value,
        )

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def get_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """Dataset ID ile getir. Bulunamazsa None döner."""
        model = await self._session.get(DatasetModel, dataset_id)
        if model is None:
            logger.debug("dataset_not_found", dataset_id=str(dataset_id))
            return None
        return self._to_entity(model)

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def get_by_mission_id(self, mission_id: UUID) -> list[Dataset]:
        """Bir mission'a ait tüm dataset'leri getir."""
        result = await self._session.execute(
            select(DatasetModel).where(DatasetModel.mission_id == mission_id).order_by(DatasetModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_status(
        self,
        status: DatasetStatus,
        *,
        province_code: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dataset]:
        """Verilen durumdaki dataset'leri getir."""
        stmt = select(DatasetModel).where(DatasetModel.status == status.value)
        stmt = stmt.order_by(DatasetModel.created_at.asc()).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_quarantined(
        self,
        *,
        province_code: Optional[str] = None,
        limit: int = 50,
    ) -> list[Dataset]:
        """REJECTED_QUARANTINE durumundaki dataset'leri getir (KR-041)."""
        return await self.get_by_status(
            DatasetStatus.REJECTED_QUARANTINE,
            province_code=province_code,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Durum guncelleme
    # ------------------------------------------------------------------

    async def update_status(
        self,
        dataset_id: UUID,
        new_status: DatasetStatus,
    ) -> None:
        """Sadece status alanını güncelle."""
        await self._session.execute(
            update(DatasetModel).where(DatasetModel.dataset_id == dataset_id).values(status=new_status.value)
        )
        await self._session.flush()
        logger.info(
            "dataset_status_updated",
            dataset_id=str(dataset_id),
            new_status=new_status.value,
        )

    # ------------------------------------------------------------------
    # Sayac
    # ------------------------------------------------------------------

    async def count_by_status(self, status: DatasetStatus) -> int:
        """Verilen durumdaki dataset sayısını döner (SLA/monitoring)."""
        result = await self._session.execute(
            select(func.count()).select_from(DatasetModel).where(DatasetModel.status == status.value)
        )
        return result.scalar_one()
