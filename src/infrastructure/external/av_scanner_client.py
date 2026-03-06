# PATH: src/infrastructure/external/av_scanner_client.py
# DESC: Anti-virus tarama istemci adapter'i (KR-073).
"""
AV Scanner Client: iki asamali zararli yazilim taramasi icin HTTP adaptoru.

KR-073: Ham dosyalar her zaman untrusted kabul edilir.
- AV1 (EdgeKiosk): Yerel istasyonu korur; bariz zararlıyı erken yakalar.
- AV2 (Merkez Security Gateway): Ikinci kontrol + kurcalama ispati zinciri.

Retry: Transient hatalarda exponential backoff.
Tarama sonuclari icin retry yapilmaz (false negative riski).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class ScanPhase(str, Enum):
    """Tarama asamasi."""

    AV1_EDGE = "AV1_EDGE"
    AV2_CENTER = "AV2_CENTER"


class ScanVerdict(str, Enum):
    """Tarama sonucu karari."""

    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True)
class ScanResult:
    """Tek dosya tarama sonucu.

    KR-073: scan_report_edge.json / scan_report_center.json icerigine karsilik gelir.
    """

    file_path: str
    file_hash_sha256: str
    verdict: ScanVerdict
    phase: ScanPhase
    engine_name: str
    engine_version: str
    signature_date: str
    threat_name: str | None = None
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "file_path": self.file_path,
            "file_hash_sha256": self.file_hash_sha256,
            "verdict": self.verdict.value,
            "phase": self.phase.value,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "signature_date": self.signature_date,
            "threat_name": self.threat_name,
            "scanned_at": self.scanned_at.isoformat(),
        }


@dataclass(frozen=True)
class BatchScanReport:
    """Toplu tarama raporu.

    KR-073: Tum dosyalar taranmadan is akisina giremez.
    """

    batch_id: str
    phase: ScanPhase
    results: tuple[ScanResult, ...]
    all_clean: bool
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "phase": self.phase.value,
            "results": [r.to_dict() for r in self.results],
            "all_clean": self.all_clean,
            "scanned_at": self.scanned_at.isoformat(),
        }


class AVScanError(Exception):
    """AV tarama hatasi."""


class AVScannerClient:
    """Anti-virus tarama servisi HTTP adaptoru.

    KR-073: Iki asamali tarama (AV1 Edge + AV2 Center).
    Retry yalnizca baglanti hatalarinda uygulanir; tarama sonuclari icin retry yok.
    """

    def __init__(self, settings: Settings) -> None:
        self._base_url = str(getattr(settings, "av_scanner_url", "http://localhost:8400"))
        self._timeout = httpx.Timeout(float(getattr(settings, "av_scanner_timeout_seconds", 120)))
        self._api_key = ""
        api_key_attr = getattr(settings, "av_scanner_api_key", None)
        if api_key_attr is not None:
            self._api_key = (
                api_key_attr.get_secret_value() if hasattr(api_key_attr, "get_secret_value") else str(api_key_attr)
            )

    def _get_client(self) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=headers,
        )

    async def scan_file(
        self,
        file_path: str,
        file_hash: str,
        phase: ScanPhase = ScanPhase.AV2_CENTER,
    ) -> ScanResult:
        """Tek dosya taramasi.

        Args:
            file_path: Taranan dosyanin yolu.
            file_hash: Dosyanin SHA-256 hash'i.
            phase: Tarama asamasi (AV1 veya AV2).

        Returns:
            ScanResult: Tarama sonucu.

        Raises:
            AVScanError: Tarama basarisiz olursa.
        """
        logger.info(
            "av_scan.file.start",
            file_path=Path(file_path).name,
            phase=phase.value,
        )
        try:
            async with self._get_client() as client:
                response = await client.post(
                    "/api/v1/scan",
                    json={
                        "file_path": file_path,
                        "file_hash_sha256": file_hash,
                        "phase": phase.value,
                    },
                )
                response.raise_for_status()
                data = response.json()

                verdict = ScanVerdict(data.get("verdict", "ERROR"))
                result = ScanResult(
                    file_path=file_path,
                    file_hash_sha256=file_hash,
                    verdict=verdict,
                    phase=phase,
                    engine_name=data.get("engine_name", "unknown"),
                    engine_version=data.get("engine_version", "unknown"),
                    signature_date=data.get("signature_date", "unknown"),
                    threat_name=data.get("threat_name"),
                )

                logger.info(
                    "av_scan.file.complete",
                    file_path=Path(file_path).name,
                    verdict=verdict.value,
                    phase=phase.value,
                )
                return result

        except httpx.HTTPStatusError as exc:
            logger.error(
                "av_scan.file.http_error",
                status_code=exc.response.status_code,
                phase=phase.value,
            )
            raise AVScanError(f"AV tarama HTTP hatasi: {exc.response.status_code}") from exc
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.error("av_scan.file.connection_error", phase=phase.value)
            raise AVScanError(f"AV tarama baglanti hatasi: {exc}") from exc

    async def scan_batch(
        self,
        batch_id: str,
        files: list[dict[str, str]],
        phase: ScanPhase = ScanPhase.AV2_CENTER,
    ) -> BatchScanReport:
        """Toplu dosya taramasi.

        Args:
            batch_id: Batch kimliği.
            files: [{"path": "...", "hash": "..."}] listesi.
            phase: Tarama asamasi.

        Returns:
            BatchScanReport: Toplu tarama raporu.
        """
        results: list[ScanResult] = []
        for file_info in files:
            result = await self.scan_file(
                file_path=file_info["path"],
                file_hash=file_info["hash"],
                phase=phase,
            )
            results.append(result)

        all_clean = all(r.verdict == ScanVerdict.CLEAN for r in results)

        logger.info(
            "av_scan.batch.complete",
            batch_id=batch_id,
            total_files=len(results),
            clean_count=sum(1 for r in results if r.verdict == ScanVerdict.CLEAN),
            infected_count=sum(1 for r in results if r.verdict == ScanVerdict.INFECTED),
            phase=phase.value,
        )

        return BatchScanReport(
            batch_id=batch_id,
            phase=phase,
            results=tuple(results),
            all_clean=all_clean,
        )

    @_RETRY_DECORATOR
    async def health_check(self) -> bool:
        """AV tarama servisi saglik kontrolu."""
        try:
            async with self._get_client() as client:
                response = await client.get("/health")
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            return False
