# PATH: src/core/ports/repositories/mission_repository.py
# DESC: MissionRepository portu.
# SSOT: KR-028 (mission yaşam döngüsü), KR-033 (ödeme hard gate)
"""
MissionRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Mission entity'sinin kalıcı depolama erişimini soyutlar.
  Analiz görevlerinin oluşturulması, güncellenmesi ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (mission_id, field_id, pilot_id vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[Mission]).

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

from src.core.domain.entities.mission import Mission, MissionStatus


class MissionRepository(ABC):
    """Mission persistence port (KR-028, KR-033).

    Analiz görevlerinin kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-033: PAID olmadan Mission ASSIGNED olamaz (ödeme doğrulama caller sorumluluğunda).
    Idempotency: mission_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, mission: Mission) -> None:
        """Mission kaydet (insert veya update).

        Args:
            mission: Kaydedilecek Mission entity'si.

        Raises:
            IntegrityError: mission_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, mission_id: uuid.UUID) -> Optional[Mission]:
        """mission_id ile Mission getir.

        Args:
            mission_id: Aranacak görev ID'si.

        Returns:
            Mission veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_field_id(self, field_id: uuid.UUID) -> List[Mission]:
        """Bir tarlaya ait tüm görevleri getir.

        Args:
            field_id: İlişkili Field ID'si.

        Returns:
            Mission listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_pilot_id(
        self,
        pilot_id: uuid.UUID,
        *,
        status: Optional[MissionStatus] = None,
    ) -> List[Mission]:
        """Bir pilota atanmış görevleri getir (durum filtresi opsiyonel).

        Args:
            pilot_id: İlişkili Pilot ID'si.
            status: Opsiyonel durum filtresi.

        Returns:
            Mission listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_status(self, status: MissionStatus) -> List[Mission]:
        """Belirli durumdaki tüm görevleri getir.

        Kuyruk yönetimi, SLA takibi ve iş dağıtımı için kullanılır.

        Args:
            status: Görev durumu (KR-028 kanonik durumlar).

        Returns:
            Mission listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_requested_by_user_id(self, user_id: uuid.UUID) -> List[Mission]:
        """Bir kullanıcının talep ettiği tüm görevleri getir.

        Args:
            user_id: Talebi oluşturan User ID'si.

        Returns:
            Mission listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_subscription_id(self, subscription_id: uuid.UUID) -> List[Mission]:
        """Bir aboneliğe bağlı tüm görevleri getir.

        Args:
            subscription_id: İlişkili Subscription ID'si.

        Returns:
            Mission listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, mission_id: uuid.UUID) -> None:
        """Mission sil.

        Args:
            mission_id: Silinecek görev ID'si.

        Raises:
            KeyError: mission_id bulunamadığında.
        """
