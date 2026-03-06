# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/ports/external/av_scanner_port.py
# DESC: AVScannerPort; KR-073 iki aşamalı malware tarama port'u.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-073 (Malware tarama), KR-070 (Worker izolasyon)
"""
AVScannerPort port (Protocol).

KR-073: İki aşamalı malware tarama.
  AV1 — Edge Kiosk: RAW_INGESTED → RAW_SCANNED_EDGE_OK
  AV2 — Merkez:     CALIBRATED  → CALIBRATED_SCANNED_CENTER_OK

Modlar:
  SMART  — Varsayılan. Şüpheli koşullarda tam tarama.
           Untrusted dosya parse işlemi izole sandbox'ta yapılır.
  BYPASS — Sadece hash+MIME kontrolü.
           CENTRAL_ADMIN yetkisi, 72 saat max, il kapsamlı (KR-073).

Tarama sonuçları:
  CLEAN      — Temiz, geçişe izin ver.
  SUSPICIOUS — Şüpheli; SMART modda tam tarama tetikler.
  INFECTED   — Virüs/malware tespiti; BLOK + REJECTED_QUARANTINE.
  ERROR      — Tarama başarısız; güvenli tarafta kal, quarantine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from src.core.domain.value_objects.av_scan_mode import AVScanConfig, AVScanMode


class AVScanResult(str, Enum):
    """AV tarama sonucu."""

    CLEAN = "CLEAN"
    SUSPICIOUS = "SUSPICIOUS"
    INFECTED = "INFECTED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class AVScanReport:
    """Tek bir tarama oturumunun raporu.

    KR-072: Bu raporun URI'si dataset.av1_report_uri veya av2_report_uri'ye yazılır.
    """

    scan_id: UUID
    dataset_id: UUID
    scanner_layer: str  # "AV1_EDGE" veya "AV2_CENTER"
    result: AVScanResult
    mode_used: AVScanMode  # Hangi mod kullanıldı
    report_uri: str  # Object Storage'daki rapor URI'si (immutable)
    scanned_at: str  # ISO-8601 UTC
    threat_name: Optional[str] = None  # INFECTED ise tespit edilen tehdit
    mime_type: Optional[str] = None
    sha256_hash: Optional[str] = None
    error_detail: Optional[str] = None  # ERROR ise hata detayı


@runtime_checkable
class AVScannerPort(Protocol):
    """Malware tarama dış port (KR-073).

    Implementation:
      src/infrastructure/external/av_scanner_adapter.py

    Worker izolasyon notu (KR-070):
      Bu port sadece EdgeKiosk (AV1) ve Platform merkez (AV2) tarafından çağrılır.
      Worker servisi bu port'u ÇAĞIRMAZ — Worker sadece queue'dan consume eder.
    """

    async def scan_raw_dataset(
        self,
        dataset_id: UUID,
        storage_path: str,
        config: AVScanConfig,
    ) -> AVScanReport:
        """AV1 (Edge) taraması: RAW dosyayı tara.

        Args:
            dataset_id: Taranan dataset.
            storage_path: Object Storage'daki dosya yolu (read-only erişim).
            config: Aktif AV konfigürasyonu (SMART veya BYPASS).

        Returns:
            AVScanReport: Tarama sonucu ve rapor URI'si.

        Note:
            SMART modda şüpheli dosyalar izole sandbox'ta parse edilir.
            BYPASS modda sadece hash+MIME kontrolü yapılır.
            INFECTED → otomatik REJECTED_QUARANTINE; çağıran servis geçişi uygular.
        """
        ...

    async def scan_calibrated_dataset(
        self,
        dataset_id: UUID,
        storage_path: str,
        config: AVScanConfig,
    ) -> AVScanReport:
        """AV2 (Merkez) taraması: Kalibre edilmiş dosyayı tara.

        Args:
            dataset_id: Taranan dataset.
            storage_path: Object Storage'daki kalibre edilmiş dosya yolu.
            config: Aktif AV konfigürasyonu.

        Returns:
            AVScanReport: Tarama sonucu ve rapor URI'si.

        Note:
            AV2 merkez taraması, Pix4Dfields kalibrasyon çıktısına uygulanır.
            Sonuç raporu dataset.av2_report_uri'ye yazılır.
        """
        ...

    async def get_report(self, scan_id: UUID) -> Optional[AVScanReport]:
        """Önceki tarama raporunu getir."""
        ...
