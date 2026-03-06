# PATH: src/core/domain/services/confidence_evaluator.py
# DESC: YZ confidence değerlendirme ve expert escalation kararı (KR-019).

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum


class ConfidenceEvaluationError(Exception):
    """Confidence değerlendirme domain invariant ihlali."""


class EscalationLevel(Enum):
    """Expert escalation seviyeleri."""

    NONE = "none"
    STANDARD = "standard"  # Tek expert review yeterli
    PRIORITY = "priority"  # Deneyimli expert gerekli
    CRITICAL = "critical"  # Birden fazla expert review gerekli


@dataclass(frozen=True)
class ConfidenceThresholds:
    """Güven skoru eşik değerleri.

    Domain invariants:
    - critical < priority < standard < auto_accept
    - Tüm değerler 0.0 ile 1.0 arasında olmalıdır.
    """

    auto_accept: float = 0.85  # Bu üzerinde otomatik kabul
    standard: float = 0.70  # Bu üzerinde standart review
    priority: float = 0.50  # Bu üzerinde öncelikli review
    critical: float = 0.30  # Bu altında kritik review

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


class ConfidenceEvaluator:
    """YZ confidence değerlendirme ve expert escalation kararı servisi (KR-019).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Confidence score 0.0 ile 1.0 arasında olmalıdır.
    - Eşik altı sonuçlar expert review'a yönlendirilmelidir.
    - Escalation seviyesi score'a göre belirlenir.
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
    ) -> ConfidenceEvaluationResult:
        """Confidence score değerlendirir ve escalation kararı verir.

        Args:
            analysis_job_id: Analiz iş ID'si.
            field_id: Tarla ID'si.
            confidence_score: Model güven skoru (0.0-1.0).
            crop_type: Bitki türü (bazı bitkiler farklı eşik gerektirebilir).

        Returns:
            ConfidenceEvaluationResult: Değerlendirme sonucu.

        Raises:
            ConfidenceEvaluationError: Score geçersizse.
        """
        if not 0.0 <= confidence_score <= 1.0:
            raise ConfidenceEvaluationError(f"confidence_score 0.0-1.0 arasında olmalıdır: {confidence_score}")

        t = self._thresholds

        if confidence_score >= t.auto_accept:
            return ConfidenceEvaluationResult(
                analysis_job_id=analysis_job_id,
                field_id=field_id,
                confidence_score=confidence_score,
                needs_expert_review=False,
                escalation_level=EscalationLevel.NONE,
                threshold_used=t.auto_accept,
                reason="Güven skoru otomatik kabul eşiğinin üzerinde.",
            )

        if confidence_score >= t.standard:
            return ConfidenceEvaluationResult(
                analysis_job_id=analysis_job_id,
                field_id=field_id,
                confidence_score=confidence_score,
                needs_expert_review=True,
                escalation_level=EscalationLevel.STANDARD,
                threshold_used=t.standard,
                reason="Güven skoru standart review eşiğinde.",
            )

        if confidence_score >= t.priority:
            return ConfidenceEvaluationResult(
                analysis_job_id=analysis_job_id,
                field_id=field_id,
                confidence_score=confidence_score,
                needs_expert_review=True,
                escalation_level=EscalationLevel.PRIORITY,
                threshold_used=t.priority,
                reason="Güven skoru düşük; öncelikli expert review gerekli.",
            )

        if confidence_score >= t.critical:
            return ConfidenceEvaluationResult(
                analysis_job_id=analysis_job_id,
                field_id=field_id,
                confidence_score=confidence_score,
                needs_expert_review=True,
                escalation_level=EscalationLevel.CRITICAL,
                threshold_used=t.critical,
                reason="Güven skoru çok düşük; kritik expert review gerekli.",
            )

        # critical altı
        return ConfidenceEvaluationResult(
            analysis_job_id=analysis_job_id,
            field_id=field_id,
            confidence_score=confidence_score,
            needs_expert_review=True,
            escalation_level=EscalationLevel.CRITICAL,
            threshold_used=t.critical,
            reason="Güven skoru kritik eşiğin altında; çoklu expert review gerekli.",
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
