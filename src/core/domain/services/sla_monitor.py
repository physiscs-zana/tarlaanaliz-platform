# PATH: src/core/domain/services/sla_monitor.py
# DESC: SLA takip ve breach detection (KR-028).

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class SLAMonitorError(Exception):
    """SLA monitor domain invariant ihlali."""


class SLAStatus(Enum):
    """SLA durumu."""

    ON_TRACK = "on_track"  # SLA süresi içinde
    AT_RISK = "at_risk"  # SLA süresine yaklaşıyor
    BREACHED = "breached"  # SLA süresi aşıldı


@dataclass(frozen=True)
class SLADefinition:
    """SLA tanımı.

    Belirli bir aşama için maksimum süre tanımı.
    """

    stage_name: str  # Aşama adı (örn: data_upload, analysis, expert_review)
    max_duration_hours: int  # Maksimum süre (saat)
    warning_threshold_ratio: float = 0.80  # Uyarı eşiği (%80)

    def __post_init__(self) -> None:
        if self.max_duration_hours <= 0:
            raise SLAMonitorError("max_duration_hours > 0 olmalıdır.")
        if not 0.0 < self.warning_threshold_ratio < 1.0:
            raise SLAMonitorError("warning_threshold_ratio 0.0-1.0 (exclusive) arasında olmalıdır.")


@dataclass(frozen=True)
class SLACheckpoint:
    """SLA kontrol noktası (bir aşamanın başlangıç/bitiş zamanı)."""

    stage_name: str
    started_at: datetime
    completed_at: datetime | None = None  # None = devam ediyor


@dataclass(frozen=True)
class SLAStageResult:
    """Tek bir aşama için SLA sonucu."""

    stage_name: str
    status: SLAStatus
    elapsed_hours: float
    max_hours: int
    remaining_hours: float
    breach_amount_hours: float  # Aşma miktarı (0 = aşılmadı)


@dataclass(frozen=True)
class SLAReport:
    """Mission SLA raporu."""

    mission_id: uuid.UUID
    overall_status: SLAStatus
    stage_results: tuple[SLAStageResult, ...]
    total_elapsed_hours: float
    breached_stages: tuple[str, ...]
    at_risk_stages: tuple[str, ...]
    checked_at: datetime


class SLAMonitor:
    """SLA takip ve breach detection servisi (KR-028).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Her aşama tanımlı SLA süresine tabidir.
    - Aşılan SLA'lar breach olarak raporlanır.
    - Warning eşiğine yaklaşan aşamalar at_risk olarak işaretlenir.
    - Overall status en kötü aşama durumuna göre belirlenir.
    """

    def __init__(self, definitions: list[SLADefinition] | None = None) -> None:
        self._definitions: dict[str, SLADefinition] = {}
        if definitions:
            for d in definitions:
                self._definitions[d.stage_name] = d

    def add_definition(self, definition: SLADefinition) -> None:
        """SLA tanımı ekler."""
        self._definitions[definition.stage_name] = definition

    def check_stage(
        self,
        *,
        checkpoint: SLACheckpoint,
        now: datetime | None = None,
    ) -> SLAStageResult:
        """Tek bir aşamanın SLA durumunu kontrol eder.

        Args:
            checkpoint: Aşama kontrol noktası.
            now: Şu anki zaman (test için override).

        Returns:
            SLAStageResult: Aşama SLA sonucu.

        Raises:
            SLAMonitorError: Aşama tanımı yoksa.
        """
        definition = self._definitions.get(checkpoint.stage_name)
        if not definition:
            raise SLAMonitorError(f"SLA tanımı bulunamadı: {checkpoint.stage_name}")

        current_time = now or datetime.now(timezone.utc)
        end_time = checkpoint.completed_at or current_time

        elapsed = end_time - checkpoint.started_at
        elapsed_hours = elapsed.total_seconds() / 3600.0
        max_hours = definition.max_duration_hours
        remaining = max_hours - elapsed_hours

        if elapsed_hours > max_hours:
            status = SLAStatus.BREACHED
            breach_amount = elapsed_hours - max_hours
        elif elapsed_hours >= max_hours * definition.warning_threshold_ratio:
            status = SLAStatus.AT_RISK
            breach_amount = 0.0
        else:
            status = SLAStatus.ON_TRACK
            breach_amount = 0.0

        return SLAStageResult(
            stage_name=checkpoint.stage_name,
            status=status,
            elapsed_hours=round(elapsed_hours, 2),
            max_hours=max_hours,
            remaining_hours=round(max(0.0, remaining), 2),
            breach_amount_hours=round(breach_amount, 2),
        )

    def check_mission(
        self,
        *,
        mission_id: uuid.UUID,
        checkpoints: list[SLACheckpoint],
        now: datetime | None = None,
    ) -> SLAReport:
        """Mission'ın tüm aşamalarının SLA durumunu kontrol eder.

        Args:
            mission_id: Mission ID.
            checkpoints: Aşama kontrol noktaları.
            now: Şu anki zaman (test için override).

        Returns:
            SLAReport: Mission SLA raporu.
        """
        current_time = now or datetime.now(timezone.utc)

        stage_results: list[SLAStageResult] = []
        breached: list[str] = []
        at_risk: list[str] = []
        total_elapsed = 0.0

        for checkpoint in checkpoints:
            if checkpoint.stage_name not in self._definitions:
                continue

            result = self.check_stage(checkpoint=checkpoint, now=current_time)
            stage_results.append(result)
            total_elapsed += result.elapsed_hours

            if result.status == SLAStatus.BREACHED:
                breached.append(result.stage_name)
            elif result.status == SLAStatus.AT_RISK:
                at_risk.append(result.stage_name)

        # Overall status: en kötü durum
        if breached:
            overall = SLAStatus.BREACHED
        elif at_risk:
            overall = SLAStatus.AT_RISK
        else:
            overall = SLAStatus.ON_TRACK

        return SLAReport(
            mission_id=mission_id,
            overall_status=overall,
            stage_results=tuple(stage_results),
            total_elapsed_hours=round(total_elapsed, 2),
            breached_stages=tuple(breached),
            at_risk_stages=tuple(at_risk),
            checked_at=current_time,
        )

    def time_until_breach(
        self,
        checkpoint: SLACheckpoint,
        now: datetime | None = None,
    ) -> timedelta | None:
        """Breach'e kalan süreyi hesaplar.

        Args:
            checkpoint: Aşama kontrol noktası.
            now: Şu anki zaman.

        Returns:
            Kalan süre veya None (zaten breach).
        """
        definition = self._definitions.get(checkpoint.stage_name)
        if not definition:
            return None

        current_time = now or datetime.now(timezone.utc)
        if checkpoint.completed_at:
            return None  # Tamamlanmış aşama

        deadline = checkpoint.started_at + timedelta(hours=definition.max_duration_hours)
        remaining = deadline - current_time

        if remaining.total_seconds() <= 0:
            return None  # Zaten breach

        return remaining
