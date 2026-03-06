# PATH: src/core/ports/external/parcel_geometry_provider.py
# DESC: ParcelGeometryProvider portu: TKGM/MEGSİS parsel geometrisi.
# SSOT: KR-013 (tarla yönetimi), KR-016 (eşleştirme), KR-080 (teknik kurallar)
"""
ParcelGeometryProvider portu: TKGM/MEGSİS parsel geometrisi.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  TKGM/MEGSİS WFS/WMS proxy üzerinden kadastro parsel geometrisi
  sorgulamayı soyutlar. Tarla kaydı ve doğrulaması için kullanılır.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (ParcelRef value object).
  Çıktı: IO sonuçları (GeoJSON polygon, alan doğrulama, parsel varlık kontrolü).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: parsel bilgileri konum verisidir, kişisel veri değildir.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). TKGM servis kesintileri için graceful degradation.

Observability (log fields/metrics/traces):
  latency, error_code, retries, parcel_ref (composite key), cache_hit.

Testler: Contract test (port), integration test (WFS stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from src.core.domain.value_objects.parcel_ref import ParcelRef


# ------------------------------------------------------------------
# Port-specific DTOs (Contract nesneleri)
# ------------------------------------------------------------------
@dataclass(frozen=True)
class ParcelGeometry:
    """TKGM/MEGSİS'ten dönen parsel geometrisi.

    geometry: GeoJSON Polygon formatında geometri.
    area_m2: Kadastro kayıtlı alan (m²).
    coordinate_system: Koordinat referans sistemi (varsayılan EPSG:4326).
    PII içermez; yalnızca konum verisi taşır.
    """

    parcel_ref: ParcelRef
    geometry: dict[str, Any]  # GeoJSON Polygon
    area_m2: Decimal
    coordinate_system: str = "EPSG:4326"

    def __post_init__(self) -> None:
        if self.area_m2 is not None and self.area_m2 <= 0:
            raise ValueError("area_m2 must be positive")


@dataclass(frozen=True)
class ParcelValidationResult:
    """Parsel doğrulama sonucu.

    exists: Parsel TKGM kaydında var mı.
    area_m2: Kadastro kayıtlı alan (varsa).
    area_deviation_pct: Kullanıcı beyanı ile kadastro arasındaki sapma (%).
    """

    exists: bool
    parcel_ref: ParcelRef
    area_m2: Optional[Decimal] = None
    area_deviation_pct: Optional[Decimal] = None
    message: str = ""


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class ParcelGeometryProvider(ABC):
    """TKGM/MEGSİS Parsel Geometri portu.

    Türkiye kadastro sisteminden parsel geometrisi ve alan bilgisi
    sorgular. Tarla kaydında (KR-013) ve eşleştirmede (KR-016)
    kullanılır.

    Infrastructure katmanı bu interface'i implemente eder:
      - TKGM WFS/WMS proxy üzerinden HTTP çağrısı
      - Cache katmanı (parsel geometrisi nadiren değişir)
      - Fallback: önceden cache'lenmiş veri

    Idempotency: Sorgu niteliğinde; doğal olarak idempotent.
    Retry: Transient hatalarda exponential backoff ile yeniden denenir.
    """

    # ------------------------------------------------------------------
    # Geometri sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_geometry(
        self,
        parcel_ref: ParcelRef,
    ) -> Optional[ParcelGeometry]:
        """Parsel geometrisini TKGM/MEGSİS'ten sorgula.

        Args:
            parcel_ref: İl/ilçe/köy/ada/parsel bilgilerini içeren referans.

        Returns:
            ParcelGeometry: GeoJSON polygon + alan bilgisi.
            None: Parsel bulunamadığında.

        Raises:
            TimeoutError: TKGM servisi yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Parsel varlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def validate_parcel(
        self,
        parcel_ref: ParcelRef,
        declared_area_m2: Optional[Decimal] = None,
    ) -> ParcelValidationResult:
        """Parsel varlığını ve alan tutarlılığını doğrula (KR-013).

        Kullanıcının beyan ettiği alanla kadastro kaydını karşılaştırır.

        Args:
            parcel_ref: Doğrulanacak parsel referansı.
            declared_area_m2: Kullanıcının beyan ettiği alan (opsiyonel).

        Returns:
            ParcelValidationResult: Varlık + alan sapması bilgisi.

        Raises:
            TimeoutError: TKGM servisi yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Toplu geometri sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_geometries_batch(
        self,
        parcel_refs: list[ParcelRef],
    ) -> list[ParcelGeometry]:
        """Birden fazla parselin geometrisini toplu sorgula.

        Bulunamayan parseller sonuç listesine dahil edilmez.

        Args:
            parcel_refs: Sorgulanacak parsel referansları listesi.

        Returns:
            list[ParcelGeometry]: Bulunan parsellerin geometrileri.

        Raises:
            TimeoutError: TKGM servisi yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """TKGM/MEGSİS servisinin erişilebilirliğini kontrol et.

        Returns:
            True: Servis sağlıklı ve erişilebilir.
            False: Servis erişilemez veya hata durumunda.
        """
