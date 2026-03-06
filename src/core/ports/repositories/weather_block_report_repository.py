# PATH: src/core/ports/repositories/weather_block_report_repository.py
# DESC: WeatherBlockReportRepository portu.
# SSOT: KR-015-5 (hava engeli reschedule token tüketmez)
"""
WeatherBlockReportRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  WeatherBlockReport entity'sinin kalıcı depolama erişimini soyutlar.
  Hava engeli raporlarının oluşturulması, güncellenmesi ve sorgulanmasını kapsar.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (weather_block_id, mission_id, field_id vb.).
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


class WeatherBlockReportRepository(ABC):
    """WeatherBlockReport persistence port (KR-015-5).

    Hava engeli raporlarının kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-015-5: Weather Block nedeniyle erteleme reschedule token tüketmez.
    Idempotency: weather_block_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, report: WeatherBlockReport) -> None:
        """WeatherBlockReport kaydet (insert veya update).

        Args:
            report: Kaydedilecek WeatherBlockReport entity'si.

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
            weather_block_id: Aranacak hava engeli rapor ID'si.

        Returns:
            WeatherBlockReport veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_mission_id(self, mission_id: uuid.UUID) -> List[WeatherBlockReport]:
        """Bir göreve ait tüm hava engeli raporlarını getir.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            WeatherBlockReport listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_field_id(self, field_id: uuid.UUID) -> List[WeatherBlockReport]:
        """Bir tarlaya ait tüm hava engeli raporlarını getir.

        Args:
            field_id: İlişkili Field ID'si.

        Returns:
            WeatherBlockReport listesi (boş olabilir).
        """

    @abstractmethod
    async def list_unresolved_by_mission_id(self, mission_id: uuid.UUID) -> List[WeatherBlockReport]:
        """Bir göreve ait çözülmemiş (resolved=False) hava engeli raporlarını getir.

        Görev yeniden planlanmadan önce aktif engel kontrolü için kullanılır.

        Args:
            mission_id: İlişkili Mission ID'si.

        Returns:
            Çözülmemiş WeatherBlockReport listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, weather_block_id: uuid.UUID) -> None:
        """WeatherBlockReport sil.

        Args:
            weather_block_id: Silinecek hava engeli rapor ID'si.

        Raises:
            KeyError: weather_block_id bulunamadığında.
        """
