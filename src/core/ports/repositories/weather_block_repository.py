# PATH: src/core/ports/repositories/weather_block_repository.py
# DESC: WeatherBlockRepository portu.
# SSOT: KR-015-5 (hava engeli yönetimi), KR-028 (mission lifecycle)
"""
WeatherBlockRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  WeatherBlockReport entity'sinin durum yönetimi ve genişletilmiş sorgularını soyutlar.
  WeatherBlockStatus yaşam döngüsü ile entegre çalışır.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (weather_block_id, status vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[WeatherBlockReport]).

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

from src.core.domain.entities.weather_block_report import WeatherBlockReport
from src.core.domain.value_objects.weather_block_status import WeatherBlockStatus


class WeatherBlockRepository(ABC):
    """WeatherBlock persistence port (KR-015-5, KR-028).

    Hava engeli kayıtlarının durum bazlı sorgularını ve yaşam döngüsü
    yönetimini soyutlar. Infrastructure katmanı bu interface'i implemente eder.

    KR-015-5: CONFIRMED weather block, force majeure; reschedule token tüketmez.
    KR-028: PENDING/CONFIRMED bloklar görevi engeller.
    Idempotency: weather_block_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, block: WeatherBlockReport) -> None:
        """WeatherBlockReport kaydet (insert veya update).

        Args:
            block: Kaydedilecek WeatherBlockReport entity'si.

        Raises:
            IntegrityError: weather_block_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, weather_block_id: uuid.UUID) -> Optional[WeatherBlockReport]:
        """weather_block_id ile WeatherBlockReport getir.

        Args:
            weather_block_id: Aranacak hava engeli ID'si.

        Returns:
            WeatherBlockReport veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_status(self, status: WeatherBlockStatus) -> List[WeatherBlockReport]:
        """Belirli durumdaki tüm hava engeli kayıtlarını getir.

        Admin paneli, raporlama ve toplu durum geçişleri için kullanılır.

        Args:
            status: Hava engeli durumu (KR-015-5 kanonik durumlar).

        Returns:
            WeatherBlockReport listesi (boş olabilir).
        """

    @abstractmethod
    async def list_blocking_by_mission_id(self, mission_id: uuid.UUID) -> List[WeatherBlockReport]:
        """Bir görevi engelleyen (PENDING/CONFIRMED) hava engeli kayıtlarını getir.

        KR-028: PENDING veya CONFIRMED durumda görev uçurulamaz.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            Engelleyici WeatherBlockReport listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_field_id(
        self,
        field_id: uuid.UUID,
        *,
        status: Optional[WeatherBlockStatus] = None,
    ) -> List[WeatherBlockReport]:
        """Bir tarlaya ait hava engeli kayıtlarını getir (durum filtresi opsiyonel).

        Args:
            field_id: İlişkili Field ID'si.
            status: Opsiyonel durum filtresi.

        Returns:
            WeatherBlockReport listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, weather_block_id: uuid.UUID) -> None:
        """WeatherBlockReport sil.

        Args:
            weather_block_id: Silinecek hava engeli ID'si.

        Raises:
            KeyError: weather_block_id bulunamadığında.
        """
