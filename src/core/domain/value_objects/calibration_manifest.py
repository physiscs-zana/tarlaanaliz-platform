# PATH: src/core/domain/value_objects/calibration_manifest.py
# DESC: CalibrationManifest VO; radyometrik kalibrasyon kanıt paketi (KR-018).

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar


class CalibrationManifestError(Exception):
    """CalibrationManifest domain invariant ihlali."""


@dataclass(frozen=True)
class CalibrationManifest:
    """Radyometrik kalibrasyon kanıt paketi (KR-018, KR-082).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    KR-018 Hard Gate kuralı:
    - Calibrated Dataset üretilmeden AnalysisJob başlatılamaz.
    - Worker, raw DN (Digital Number) veya belirsiz kalibrasyon verisi reddeder.
    - Platform: requires_calibrated=true olmadan job açılamaz.

    İstasyon akışı (KR-016/KR-017, M1+M2 mimarisi):
    1. M1 (İşleme İstasyonu, offline): AV tarama + manifest/hash doğrulama
    2. M1: Pix4Dfields ile tam radyometrik kalibrasyon (drone-agnostik)
    3. M2 (Gönderim İstasyonu): Calibrated Dataset + raporlar + manifest/hash -> Platform/Ingress

    Invariants:
    - manifest_hash boş olamaz (SHA-256 bütünlük kanıtı).
    - qc_result, geçerli değerlerden (PASS/WARN/FAIL) biri olmalıdır.
    - calibrated_at zorunludur.
    - file_entries en az bir dosya içermelidir.
    """

    manifest_hash: str
    qc_result: str
    calibrated_at: datetime
    calibration_tool: str
    file_entries: tuple[CalibrationFileEntry, ...]
    flags: tuple[str, ...] = ()
    recommended_action: str | None = None
    notes: str | None = None

    QC_PASS: ClassVar[str] = "PASS"
    QC_WARN: ClassVar[str] = "WARN"
    QC_FAIL: ClassVar[str] = "FAIL"

    _VALID_QC_RESULTS: ClassVar[frozenset[str]] = frozenset({"PASS", "WARN", "FAIL"})

    def __post_init__(self) -> None:
        if not self.manifest_hash or not self.manifest_hash.strip():
            raise CalibrationManifestError("manifest_hash boş olamaz (SHA-256 zorunlu).")
        if self.qc_result not in self._VALID_QC_RESULTS:
            raise CalibrationManifestError(
                f"Geçersiz qc_result: '{self.qc_result}'. "
                f"Geçerli değerler: {sorted(self._VALID_QC_RESULTS)}"
            )
        if self.calibrated_at is None:
            raise CalibrationManifestError("calibrated_at zorunludur.")
        if not self.file_entries:
            raise CalibrationManifestError("file_entries en az bir dosya içermelidir.")
        if not self.calibration_tool or not self.calibration_tool.strip():
            raise CalibrationManifestError("calibration_tool boş olamaz.")

    @property
    def is_passed(self) -> bool:
        """Kalibrasyon QC sonucu PASS mı?"""
        return self.qc_result == self.QC_PASS

    @property
    def is_warning(self) -> bool:
        """Kalibrasyon QC sonucu WARN mı?"""
        return self.qc_result == self.QC_WARN

    @property
    def is_failed(self) -> bool:
        """Kalibrasyon QC sonucu FAIL mı?"""
        return self.qc_result == self.QC_FAIL

    @property
    def allows_analysis(self) -> bool:
        """KR-018 hard gate: kalibrasyon analiz için yeterli mi?

        PASS -> izin verilir
        WARN -> izin verilir (uyarı ile)
        FAIL -> izin verilmez
        """
        return self.qc_result in {self.QC_PASS, self.QC_WARN}

    @property
    def file_count(self) -> int:
        """Manifest'teki dosya sayısı."""
        return len(self.file_entries)

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "manifest_hash": self.manifest_hash,
            "qc_result": self.qc_result,
            "calibrated_at": self.calibrated_at.isoformat(),
            "calibration_tool": self.calibration_tool,
            "file_entries": [entry.to_dict() for entry in self.file_entries],
            "flags": list(self.flags),
            "recommended_action": self.recommended_action,
            "notes": self.notes,
            "allows_analysis": self.allows_analysis,
        }

    def __repr__(self) -> str:
        return (
            f"CalibrationManifest(qc_result='{self.qc_result}', "
            f"file_count={self.file_count}, "
            f"allows_analysis={self.allows_analysis})"
        )


@dataclass(frozen=True)
class CalibrationFileEntry:
    """Kalibrasyon manifest'indeki tekil dosya kaydı.

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.

    Invariants:
    - file_name boş olamaz.
    - file_hash boş olamaz (SHA-256).
    - file_size_bytes >= 0.
    """

    file_name: str
    file_hash: str
    file_size_bytes: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.file_name or not self.file_name.strip():
            raise CalibrationManifestError("file_name boş olamaz.")
        if not self.file_hash or not self.file_hash.strip():
            raise CalibrationManifestError("file_hash boş olamaz (SHA-256 zorunlu).")
        if not isinstance(self.file_size_bytes, int) or self.file_size_bytes < 0:
            raise CalibrationManifestError(
                f"file_size_bytes negatif olamaz, alınan: {self.file_size_bytes}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "file_name": self.file_name,
            "file_hash": self.file_hash,
            "file_size_bytes": self.file_size_bytes,
            "created_at": self.created_at.isoformat(),
        }
