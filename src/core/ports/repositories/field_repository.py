# PATH: src/core/ports/repositories/field_repository.py
# DESC: FieldRepository portu.
# SSOT: KR-013 (çiftçi üyeliği / tarla yönetimi), KR-016 (eşleştirme), KR-080 (teknik kurallar)
"""
FieldRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Field entity'sinin kalıcı depolama erişimini soyutlar.
  Tarla kayıtlarının oluşturulması, güncellenmesi ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (field_id, user_id, parcel_ref vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[Field]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.entities.field import Field


class FieldRepository(ABC):
    """Field persistence port (KR-013, KR-016, KR-080).

    Tarla kayıtlarının kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    Tekil kayıt kuralı: il+ilçe+mahalle/köy+ada+parsel kombinasyonu tekrar edemez (KR-080).
    Idempotency: field_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, field: Field) -> None:
        """Field kaydet (insert veya update).

        Args:
            field: Kaydedilecek Field entity'si.

        Raises:
            IntegrityError: field_id veya parcel_ref benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, field_id: uuid.UUID) -> Optional[Field]:
        """field_id ile Field getir.

        Args:
            field_id: Aranacak tarla ID'si.

        Returns:
            Field veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_parcel_ref(
        self,
        province: str,
        district: str,
        village: str,
        ada: str,
        parsel: str,
    ) -> Optional[Field]:
        """Parsel referansı ile Field getir (KR-080 tekil kayıt kuralı).

        il+ilçe+mahalle/köy+ada+parsel kombinasyonu benzersiz olmalıdır.

        Args:
            province: İl adı.
            district: İlçe adı.
            village: Mahalle/köy adı.
            ada: Ada numarası.
            parsel: Parsel numarası.

        Returns:
            Field veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_user_id(self, user_id: uuid.UUID) -> List[Field]:
        """Bir kullanıcıya ait tüm tarlaları getir.

        Args:
            user_id: İlişkili User ID'si.

        Returns:
            Field listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_province(self, province: str) -> List[Field]:
        """Belirli bir ildeki tarlaları getir.

        Args:
            province: İl adı.

        Returns:
            Field listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, field_id: uuid.UUID) -> None:
        """Field sil.

        Args:
            field_id: Silinecek tarla ID'si.

        Raises:
            KeyError: field_id bulunamadığında.
        """
