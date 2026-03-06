# PATH: src/core/ports/repositories/price_snapshot_repository.py
# DESC: PriceSnapshotRepository portu.
# SSOT: KR-022 (fiyat yönetimi politikası), KR-033 (ödeme akışı)
"""
PriceSnapshotRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  PriceSnapshot entity'sinin kalıcı depolama erişimini soyutlar.
  Fiyat snapshot'larının oluşturulması ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (price_snapshot_id, crop_type, analysis_type vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[PriceSnapshot]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: fiyat verisi PII değildir ancak ticari hassas olabilir.
  KR-022: Fiyat snapshot'ları immutable; sipariş/abonelik oluşurken snapshot siparişe yazılır.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
  KR-022: Versiyonlu + tarih aralıklı fiyat yönetimi.
  KR-033: Sipariş/abonelik oluşurken fiyat snapshot siparişe yazılır.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from src.core.domain.entities.price_snapshot import PriceSnapshot


class PriceSnapshotRepository(ABC):
    """PriceSnapshot persistence port (KR-022, KR-033).

    Fiyat snapshot'larının kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-022: PriceSnapshot immutable (frozen); geçmiş siparişlerin fiyatı değişmez.
    Idempotency: price_snapshot_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, snapshot: PriceSnapshot) -> None:
        """PriceSnapshot kaydet (insert).

        PriceSnapshot frozen/immutable olduğundan update desteklenmez;
        yeni fiyat için yeni snapshot oluşturulur (KR-022).

        Args:
            snapshot: Kaydedilecek PriceSnapshot entity'si.

        Raises:
            IntegrityError: price_snapshot_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, price_snapshot_id: uuid.UUID) -> Optional[PriceSnapshot]:
        """price_snapshot_id ile PriceSnapshot getir.

        Args:
            price_snapshot_id: Aranacak fiyat snapshot ID'si.

        Returns:
            PriceSnapshot veya bulunamazsa None.
        """

    @abstractmethod
    async def find_active_by_crop_and_type(
        self,
        crop_type: str,
        analysis_type: str,
        as_of: date,
    ) -> Optional[PriceSnapshot]:
        """Ürün türü ve analiz türü için belirli tarihte geçerli snapshot getir.

        Sipariş/abonelik oluşturma sırasında güncel fiyatı bulmak için kullanılır
        (KR-033).

        Args:
            crop_type: Ürün türü (ör. "wheat", "corn").
            analysis_type: Analiz türü ("single" veya "seasonal").
            as_of: Geçerlilik tarihi.

        Returns:
            PriceSnapshot veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_crop_type(self, crop_type: str) -> List[PriceSnapshot]:
        """Bir ürün türüne ait tüm fiyat snapshot'larını getir.

        Args:
            crop_type: Ürün türü (ör. "wheat", "corn").

        Returns:
            PriceSnapshot listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_analysis_type(self, analysis_type: str) -> List[PriceSnapshot]:
        """Belirli analiz türündeki tüm fiyat snapshot'larını getir.

        Args:
            analysis_type: Analiz türü ("single" veya "seasonal").

        Returns:
            PriceSnapshot listesi (boş olabilir).
        """

    @abstractmethod
    async def list_active_as_of(self, as_of: date) -> List[PriceSnapshot]:
        """Belirli tarihte geçerli olan tüm fiyat snapshot'larını getir.

        Fiyat listesi görüntüleme ve raporlama için kullanılır.

        Args:
            as_of: Geçerlilik tarihi.

        Returns:
            PriceSnapshot listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, price_snapshot_id: uuid.UUID) -> None:
        """PriceSnapshot sil.

        Args:
            price_snapshot_id: Silinecek fiyat snapshot ID'si.

        Raises:
            KeyError: price_snapshot_id bulunamadığında.
        """
