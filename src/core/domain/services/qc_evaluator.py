# PATH: src/core/domain/services/qc_evaluator.py
# DESC: Kalite kontrol değerlendirme ve gate decision.

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class QCEvaluationError(Exception):
    """QC değerlendirme domain invariant ihlali."""


class QCDecision(Enum):
    """QC gate kararı."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class RecommendedAction(Enum):
    """QC sonrası önerilen aksiyon."""

    PROCEED = "proceed"  # Analize devam et
    REVIEW = "review"  # Manuel inceleme gerekli
    RECAPTURE = "recapture"  # Yeniden veri toplama gerekli
    RECALIBRATE = "recalibrate"  # Yeniden kalibrasyon gerekli


@dataclass(frozen=True)
class QCMetric:
    """Tek bir QC metrik ölçümü."""

    metric_name: str
    value: float
    threshold_min: float | None  # None = alt sınır yok
    threshold_max: float | None  # None = üst sınır yok
    weight: float = 1.0  # Ağırlık (toplam skora katkı)

    @property
    def is_within_bounds(self) -> bool:
        """Metrik değeri eşik sınırları içinde mi."""
        if self.threshold_min is not None and self.value < self.threshold_min:
            return False
        if self.threshold_max is not None and self.value > self.threshold_max:
            return False
        return True


@dataclass(frozen=True)
class QCFlag:
    """QC kontrol bayrağı."""

    flag_name: str
    severity: str  # INFO | WARNING | ERROR
    description: str


@dataclass(frozen=True)
class QCEvaluationResult:
    """QC değerlendirme sonucu.

    KR-018: FAIL durumunda AnalysisJob başlatılamaz (hard gate).
    """

    mission_id: uuid.UUID
    batch_id: uuid.UUID
    decision: QCDecision
    recommended_action: RecommendedAction
    overall_score: float  # 0.0 - 1.0
    metrics: tuple[QCMetric, ...]
    flags: tuple[QCFlag, ...]
    evaluated_at: datetime

    @property
    def allows_analysis(self) -> bool:
        """KR-018 hard gate: analiz başlatılabilir mi."""
        return self.decision in (QCDecision.PASS, QCDecision.WARN)


class QCEvaluator:
    """Kalite kontrol değerlendirme ve gate decision servisi.

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.
    KR-018 hard gate: calibrated/QC kanıtı olmadan AnalysisJob başlatılmamalıdır.

    Domain invariants:
    - Tüm zorunlu metrikler sağlanmalıdır.
    - FAIL kararı analiz başlatmayı engeller (hard gate).
    - Overall score tüm metriklerin ağırlıklı ortalamasıdır.
    - Her metrik kendi eşik değerleri ile değerlendirilir.
    """

    # Varsayılan QC eşikleri
    DEFAULT_PASS_THRESHOLD: float = 0.80  # Bu üzerinde PASS
    DEFAULT_WARN_THRESHOLD: float = 0.60  # Bu üzerinde WARN, altında FAIL

    def __init__(
        self,
        pass_threshold: float | None = None,
        warn_threshold: float | None = None,
    ) -> None:
        self._pass_threshold = pass_threshold if pass_threshold is not None else self.DEFAULT_PASS_THRESHOLD
        self._warn_threshold = warn_threshold if warn_threshold is not None else self.DEFAULT_WARN_THRESHOLD
        if self._warn_threshold >= self._pass_threshold:
            raise QCEvaluationError("warn_threshold, pass_threshold'dan küçük olmalıdır.")

    def evaluate(
        self,
        *,
        mission_id: uuid.UUID,
        batch_id: uuid.UUID,
        metrics: list[QCMetric],
    ) -> QCEvaluationResult:
        """QC metriklerini değerlendirir ve gate kararı verir.

        Args:
            mission_id: Mission ID.
            batch_id: Veri batch ID.
            metrics: QC metrikleri listesi.

        Returns:
            QCEvaluationResult: Değerlendirme sonucu.

        Raises:
            QCEvaluationError: Metrik listesi boşsa.
        """
        if not metrics:
            raise QCEvaluationError("En az bir QC metrik gereklidir.")

        flags: list[QCFlag] = []
        has_critical_failure = False

        # Metrik bazında kontrol
        for metric in metrics:
            if not metric.is_within_bounds:
                if metric.weight >= 0.8:
                    has_critical_failure = True
                    flags.append(
                        QCFlag(
                            flag_name=metric.metric_name,
                            severity="ERROR",
                            description=(
                                f"{metric.metric_name}: değer {metric.value:.4f} "
                                f"eşik dışında "
                                f"(min={metric.threshold_min}, max={metric.threshold_max})."
                            ),
                        )
                    )
                else:
                    flags.append(
                        QCFlag(
                            flag_name=metric.metric_name,
                            severity="WARNING",
                            description=(
                                f"{metric.metric_name}: değer {metric.value:.4f} eşik dışında (düşük ağırlık)."
                            ),
                        )
                    )

        # Overall score hesaplama (ağırlıklı)
        overall_score = self._calculate_overall_score(metrics)

        # Karar verme
        if has_critical_failure or overall_score < self._warn_threshold:
            decision = QCDecision.FAIL
            recommended_action = RecommendedAction.RECAPTURE
        elif overall_score < self._pass_threshold:
            decision = QCDecision.WARN
            recommended_action = RecommendedAction.REVIEW
        else:
            decision = QCDecision.PASS
            recommended_action = RecommendedAction.PROCEED

        return QCEvaluationResult(
            mission_id=mission_id,
            batch_id=batch_id,
            decision=decision,
            recommended_action=recommended_action,
            overall_score=overall_score,
            metrics=tuple(metrics),
            flags=tuple(flags),
            evaluated_at=datetime.now(timezone.utc),
        )

    def _calculate_overall_score(self, metrics: list[QCMetric]) -> float:
        """Metriklerin ağırlıklı ortalamasını hesaplar.

        Her metrik kendi eşik değerleri içindeyse 1.0, dışındaysa
        sapma oranına göre 0.0-1.0 arası skor alır.
        """
        total_weight = sum(m.weight for m in metrics)
        if total_weight == 0:
            return 0.0

        weighted_sum = 0.0
        for metric in metrics:
            if metric.is_within_bounds:
                weighted_sum += metric.weight * 1.0
            else:
                # Sapma oranına göre kısmi skor
                deviation = self._calculate_deviation(metric)
                partial_score = max(0.0, 1.0 - deviation)
                weighted_sum += metric.weight * partial_score

        return weighted_sum / total_weight

    @staticmethod
    def _calculate_deviation(metric: QCMetric) -> float:
        """Metrik değerinin eşik dışı sapma oranını hesaplar (0.0 - 1.0+)."""
        if metric.threshold_min is not None and metric.value < metric.threshold_min:
            if metric.threshold_min == 0:
                return abs(metric.value)
            return abs(metric.threshold_min - metric.value) / abs(metric.threshold_min)

        if metric.threshold_max is not None and metric.value > metric.threshold_max:
            if metric.threshold_max == 0:
                return abs(metric.value)
            return abs(metric.value - metric.threshold_max) / abs(metric.threshold_max)

        return 0.0

    def can_start_analysis(self, result: QCEvaluationResult) -> bool:
        """KR-018 hard gate: analiz başlatılabilir mi."""
        return result.allows_analysis
