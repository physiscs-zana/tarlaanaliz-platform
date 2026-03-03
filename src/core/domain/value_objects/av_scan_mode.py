# PATH: src/core/domain/value_objects/av_scan_mode.py
# DESC: AVScanMode VO; KR-073 malware tarama modu.
# SSOT: TARLAANALIZ_SSOT_v1_1_0.txt — KR-073 (İki aşamalı malware tarama)
"""
AVScanMode value object.

KR-073: İki aşamalı malware tarama sistemi.

Tarama katmanları:
  AV1 — Edge Kiosk (ilk alım noktası, RAW_INGESTED → RAW_SCANNED_EDGE_OK)
  AV2 — Merkez / Center (kalibrasyon sonrası, CALIBRATED → CALIBRATED_SCANNED_CENTER_OK)

Modlar:
  SMART  — Varsayılan. Şüpheli koşullarda tam tarama yapar.
           Untrusted dosya parse işlemi izole sandbox'ta.
           EICAR veya gerçek virüs tespitinde: BLOK + REJECTED_QUARANTINE.

  BYPASS — Yalnızca hash + MIME kontrolü (tam AV taraması atlanır).
           Sadece CENTRAL_ADMIN aktif edebilir.
           Maksimum 72 saat geçerli.
           İl (province) kapsamında geçerli.
           Süre dolunca otomatik SMART'a döner.
           Audit log'a zorunlu olarak yazılır (WORM).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import UUID


class AVScanModeError(Exception):
    """AVScanMode domain invariant ihlali."""


class AVScanMode(str, Enum):
    """Malware tarama modu (KR-073).

    SMART  — Tam AV taraması (varsayılan).
    BYPASS — Hash+MIME kontrolü (CENTRAL_ADMIN, 72saat max, il-kapsamlı).
    """

    SMART = "SMART"
    BYPASS = "BYPASS"


# BYPASS modunun maksimum süresi
BYPASS_MAX_DURATION: timedelta = timedelta(hours=72)


@dataclass(frozen=True)
class AVScanConfig:
    """Aktif AV tarama konfigürasyonu.

    SMART mod için sadece mode=SMART yeterli.
    BYPASS mod için: mode=BYPASS + yetkili + bitiş zamanı + il zorunlu.
    """

    mode: AVScanMode
    authorized_by: Optional[UUID] = None    # CENTRAL_ADMIN user_id
    expires_at: Optional[datetime] = None   # UTC; BYPASS için zorunlu
    province_code: Optional[str] = None     # BYPASS kapsamı (il kodu)

    def __post_init__(self) -> None:
        if self.mode == AVScanMode.BYPASS:
            if self.authorized_by is None:
                raise AVScanModeError(
                    "BYPASS modu için authorized_by (CENTRAL_ADMIN) zorunludur"
                )
            if self.expires_at is None:
                raise AVScanModeError(
                    "BYPASS modu için expires_at zorunludur"
                )
            if self.province_code is None or not self.province_code.strip():
                raise AVScanModeError(
                    "BYPASS modu için province_code (il kapsamı) zorunludur"
                )
            # 72 saat sınırı kontrolü
            if self.authorized_by is not None and self.expires_at is not None:
                now = datetime.now(timezone.utc)
                max_expiry = now + BYPASS_MAX_DURATION
                if self.expires_at > max_expiry:
                    raise AVScanModeError(
                        f"BYPASS süresi maksimum {BYPASS_MAX_DURATION} olabilir (KR-073)"
                    )

    @property
    def is_active_bypass(self) -> bool:
        """BYPASS mod şu an aktif mi?"""
        if self.mode != AVScanMode.BYPASS:
            return False
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_expired(self) -> bool:
        """BYPASS süresi doldu mu? (Otomatik SMART'a dönülür.)"""
        if self.mode == AVScanMode.SMART:
            return False
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) >= self.expires_at

    def effective_mode(self) -> AVScanMode:
        """Güncel efektif mod: BYPASS süresi dolduysa SMART döner."""
        if self.mode == AVScanMode.BYPASS and self.is_expired:
            return AVScanMode.SMART
        return self.mode

    @classmethod
    def default_smart(cls) -> "AVScanConfig":
        """Varsayılan SMART mod konfigürasyonu."""
        return cls(mode=AVScanMode.SMART)
