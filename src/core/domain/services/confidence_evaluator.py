# PATH: src/core/domain/services/confidence_evaluator.py
# DESC: YZ confidence değerlendirme ve expert escalation kararı (KR-019).
# KR-019 v1.2.0: Worker fail-closed seviyeleri ile hizalanmış eşikler.
# Eşik kaynağı: config/dynamic_thresholds.yaml (Worker) — Platform aynı sınırları kullanır.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class ConfidenceEvaluationError(Exception):
    """Confidence değerlendirme domain invariant ihlali."""


class EscalationLevel(Enum):
    """Expert escalation seviyeleri."""

    NONE = "none"
    STANDARD = "standard"  # Tek expert review yeterli
    PRIORITY = "priority"  # Deneyimli expert gerekli
    CRITICAL = "critical"  # Birden fazla expert review gerekli


class EscalationReason(str, Enum):
    """Worker Layer 2 escalation triggers (KR-019).

    Platform mirrors Worker's EscalationReason enum to understand
    WHY Worker escalated, not just the confidence score.
    """

    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    LOW_AGREEMENT = "LOW_AGREEMENT"
    OOD_DETECTED = "OOD_DETECTED"
    HIGH_EPISTEMIC = "HIGH_EPISTEMIC"
    EXPERT_RE_TRIGGER = "EXPERT_RE_TRIGGER"


# KR-019 canonical severity boosters: these reasons indicate severe model
# uncertainty beyond what confidence score alone captures.
_SEVERITY_BOOSTING_REASONS: frozenset[EscalationReason] = frozenset({
    EscalationReason.OOD_DETECTED,
    EscalationReason.HIGH_EPISTEMIC,
    EscalationReason.EXPERT_RE_TRIGGER,
})


@dataclass(frozen=True)
class ConfidenceThresholds:
    """Güven skoru eşik değerleri — KR-019 fail-closed seviyeleri ile hizalı.

    Worker fail-closed mapping:
      ≥ auto_accept (global_floor) → FULL_REPORT   → EscalationLevel.NONE
      ≥ standard    (0.45)         → PARTIAL_REPORT → EscalationLevel.STANDARD
      ≥ priority    (0.25)         → INDICES_ONLY   → EscalationLevel.PRIORITY
      < priority    (< 0.25)       → NO_RESULT      → EscalationLevel.CRITICAL

    Domain invariants:
    - critical < priority < standard < auto_accept
    - Tüm değerler 0.0 ile 1.0 arasında olmalıdır.
    """

    auto_accept: float = 0.65  # KR-019 global_floor — dynamic_threshold minimum
    standard: float = 0.45     # PARTIAL_REPORT sınırı
    priority: float = 0.25     # INDICES_ONLY sınırı
    critical: float = 0.10     # NO_RESULT alt sınırı (< 0.25 tamamı CRITICAL)

    def __post_init__(self) -> None:
        for name, val in [
            ("auto_accept", self.auto_accept),
            ("standard", self.standard),
            ("priority", self.priority),
            ("critical", self.critical),
        ]:
            if not 0.0 <= val <= 1.0:
                raise ConfidenceEvaluationError(f"{name} değeri 0.0-1.0 arasında olmalıdır: {val}")
        if not (self.critical < self.priority < self.standard < self.auto_accept):
            raise ConfidenceEvaluationError("Eşik sıralaması: critical < priority < standard < auto_accept olmalıdır.")

    @classmethod
    def for_crop(cls, dynamic_threshold: float) -> ConfidenceThresholds:
        """Crop-specific dynamic threshold ile oluşturur.

        Worker'ın config/dynamic_thresholds.yaml'ından okunan crop × analysis_type
        bazlı eşik değeri auto_accept olarak kullanılır. global_floor (0.65) altına
        inemez (KR-019 güvencesi).

        Args:
            dynamic_threshold: Crop-specific threshold (e.g., 0.82 for pamuk.disease).
        """
        floor = 0.65  # KR-019 global_floor
        effective = max(dynamic_threshold, floor)
        return cls(auto_accept=effective)


@dataclass(frozen=True)
class ConfidenceEvaluationResult:
    """Confidence değerlendirme sonucu."""

    analysis_job_id: uuid.UUID
    field_id: uuid.UUID
    confidence_score: float
    needs_expert_review: bool
    escalation_level: EscalationLevel
    threshold_used: float
    reason: str
    escalation_reasons: tuple[EscalationReason, ...] = ()


class ConfidenceEvaluator:
    """YZ confidence değerlendirme ve expert escalation kararı servisi (KR-019).

    İki katmanlı değerlendirme:
    1. Confidence score → fail-closed seviye (Worker ile aynı sınırlar)
    2. Worker escalation reasons → severity booster (OOD, epistemic → seviye yükseltme)

    Eşik hizalaması (KR-019 v1.2.0):
      Worker ResultMode        | Platform EscalationLevel | Eşik
      ─────────────────────────┼──────────────────────────┼──────
      FULL_REPORT              | NONE                     | ≥ dynamic_threshold (min 0.65)
      PARTIAL_REPORT           | STANDARD                 | 0.45 – dynamic_threshold
      INDICES_ONLY             | PRIORITY                 | 0.25 – 0.45
      NO_RESULT                | CRITICAL                 | < 0.25

    Domain invariants:
    - Confidence score 0.0 ile 1.0 arasında olmalıdır.
    - Eşik altı sonuçlar expert review'a yönlendirilmelidir.
    - Worker escalation_reasons varsa, needs_expert_review = True (zorunlu).
    """

    def __init__(
        self,
        thresholds: ConfidenceThresholds | None = None,
    ) -> None:
        self._thresholds = thresholds or ConfidenceThresholds()

    @property
    def thresholds(self) -> ConfidenceThresholds:
        return self._thresholds

    def evaluate(
        self,
        *,
        analysis_job_id: uuid.UUID,
        field_id: uuid.UUID,
        confidence_score: float,
        crop_type: str = "",
        escalation_reasons: tuple[EscalationReason, ...] = (),
    ) -> ConfidenceEvaluationResult:
        """Confidence score değerlendirir ve escalation kararı verir.

        Args:
            analysis_job_id: Analiz iş ID'si.
            field_id: Tarla ID'si.
            confidence_score: Model güven skoru (0.0-1.0).
            crop_type: Bitki türü (gelecekte crop-specific threshold için).
            escalation_reasons: Worker Layer 2 tetikleyicileri (varsa).

        Returns:
            ConfidenceEvaluationResult: Değerlendirme sonucu.

        Raises:
            ConfidenceEvaluationError: Score geçersizse.
        """
        if not 0.0 <= confidence_score <= 1.0:
            raise ConfidenceEvaluationError(f"confidence_score 0.0-1.0 arasında olmalıdır: {confidence_score}")

        t = self._thresholds
        has_worker_escalation = len(escalation_reasons) > 0
        has_severe_reason = bool(set(escalation_reasons) & _SEVERITY_BOOSTING_REASONS)

        # Determine base escalation level from confidence score
        if confidence_score >= t.auto_accept:
            base_level = EscalationLevel.NONE
            threshold_used = t.auto_accept
            base_reason = "Güven skoru otomatik kabul eşiğinin üzerinde."
        elif confidence_score >= t.standard:
            base_level = EscalationLevel.STANDARD
            threshold_used = t.standard
            base_reason = "Güven skoru PARTIAL_REPORT aralığında; standart review gerekli."
        elif confidence_score >= t.priority:
            base_level = EscalationLevel.PRIORITY
            threshold_used = t.priority
            base_reason = "Güven skoru INDICES_ONLY aralığında; öncelikli expert review gerekli."
        else:
            base_level = EscalationLevel.CRITICAL
            threshold_used = t.critical
            base_reason = "Güven skoru NO_RESULT aralığında; çoklu expert review gerekli."

        # Apply Worker escalation reasons (KR-019 Layer 2)
        final_level = base_level
        reason = base_reason

        if has_worker_escalation and base_level == EscalationLevel.NONE:
            # Worker escalated despite high confidence — another trigger fired
            final_level = EscalationLevel.STANDARD
            reason = (
                f"Güven skoru yeterli ancak Worker eskalasyon tetikledi: "
                f"{', '.join(r.value for r in escalation_reasons)}."
            )

        if has_severe_reason:
            # OOD, high epistemic, or expert re-trigger → boost severity
            if final_level in (EscalationLevel.NONE, EscalationLevel.STANDARD):
                final_level = EscalationLevel.PRIORITY
                reason = (
                    f"Ciddi eskalasyon nedeni tespit edildi: "
                    f"{', '.join(r.value for r in escalation_reasons)}; "
                    f"öncelikli review'a yükseltildi."
                )
            elif final_level == EscalationLevel.PRIORITY:
                final_level = EscalationLevel.CRITICAL
                reason = (
                    f"Ciddi eskalasyon nedeni + düşük güven: "
                    f"{', '.join(r.value for r in escalation_reasons)}; "
                    f"kritik review'a yükseltildi."
                )

        needs_review = final_level != EscalationLevel.NONE

        return ConfidenceEvaluationResult(
            analysis_job_id=analysis_job_id,
            field_id=field_id,
            confidence_score=confidence_score,
            needs_expert_review=needs_review,
            escalation_level=final_level,
            threshold_used=threshold_used,
            reason=reason,
            escalation_reasons=escalation_reasons,
        )

    def requires_multiple_experts(self, result: ConfidenceEvaluationResult) -> bool:
        """Birden fazla expert review gerekip gerekmediğini belirler."""
        return result.escalation_level == EscalationLevel.CRITICAL

    def suggested_expert_count(self, result: ConfidenceEvaluationResult) -> int:
        """Önerilen expert sayısını döner."""
        match result.escalation_level:
            case EscalationLevel.NONE:
                return 0
            case EscalationLevel.STANDARD:
                return 1
            case EscalationLevel.PRIORITY:
                return 1
            case EscalationLevel.CRITICAL:
                return 2
