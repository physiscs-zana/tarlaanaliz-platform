# PATH: src/core/ports/repositories/pilot_repository.py
# DESC: PilotRepository portu (KR-015).
# SSOT: KR-015 (drone pilotları), KR-015-1 (kapasite), KR-015-2 (seed/pull)
"""
PilotRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Pilot entity'sinin kalıcı depolama erişimini soyutlar.
  Drone pilotlarının kayıt, kapasite ve bölge yönetimini kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (pilot_id, user_id, province vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[Pilot]).

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

from src.core.domain.entities.pilot import Pilot, PilotStatus


class PilotRepository(ABC):
    """Pilot persistence port (KR-015).

    Drone pilotlarının kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    Idempotency: pilot_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, pilot: Pilot) -> None:
        """Pilot kaydet (insert veya update).

        Args:
            pilot: Kaydedilecek Pilot entity'si.

        Raises:
            IntegrityError: pilot_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, pilot_id: uuid.UUID) -> Optional[Pilot]:
        """pilot_id ile Pilot getir.

        Args:
            pilot_id: Aranacak pilot ID'si.

        Returns:
            Pilot veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_user_id(self, user_id: uuid.UUID) -> Optional[Pilot]:
        """user_id ile Pilot getir.

        Bir kullanıcının pilot profilini bulmak için kullanılır.

        Args:
            user_id: İlişkili User ID'si.

        Returns:
            Pilot veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_province(self, province: str) -> List[Pilot]:
        """Belirli bir ildeki pilotları getir.

        Bölge bazlı görev ataması için kullanılır.

        Args:
            province: İl adı.

        Returns:
            Pilot listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_status(self, status: PilotStatus) -> List[Pilot]:
        """Belirli durumdaki pilotları getir.

        Args:
            status: Pilot durumu (ACTIVE, INACTIVE, SUSPENDED).

        Returns:
            Pilot listesi (boş olabilir).
        """

    @abstractmethod
    async def list_active_by_province(self, province: str) -> List[Pilot]:
        """Belirli bir ildeki aktif pilotları getir.

        Görev ataması için yalnızca aktif ve uygun pilotları listeler.

        Args:
            province: İl adı.

        Returns:
            ACTIVE durumlu Pilot listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, pilot_id: uuid.UUID) -> None:
        """Pilot sil.

        Args:
            pilot_id: Silinecek pilot ID'si.

        Raises:
            KeyError: pilot_id bulunamadığında.
        """
