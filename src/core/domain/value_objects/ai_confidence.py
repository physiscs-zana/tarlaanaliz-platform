# PATH: src/core/domain/value_objects/ai_confidence.py
# DESC: AIConfidence VO; güven skoru (0.0-1.0) ve eşik kuralları.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from src.core.domain.value_objects.confidence_score import ConfidenceScore


class AIConfidenceError(Exception):
    """AIConfidence domain invariant ihlali."""


@dataclass(frozen=True)
class AIConfidence:
    """AI model güven skoru ve eşik kuralları (KR-019, KR-081).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    ConfidenceScore'u sarmalar ve AI-spesifik eşik mantığı ekler:
    - Varsayılan expert review eşiği: 0.75 (KR-019)
    - Eşik altında kalan sonuçlar uzman incelemesine yönlendirilir.

    Invariants:
    - score, geçerli bir ConfidenceScore olmalıdır (0.0-1.0).
    - threshold, 0.0-1.0 arasında olmalıdır.
    """

    score: ConfidenceScore
    threshold: float

    DEFAULT_EXPERT_REVIEW_THRESHOLD: ClassVar[float] = 0.75

    def __post_init__(self) -> None:
        if not isinstance(self.score, ConfidenceScore):
            raise AIConfidenceError(f"score ConfidenceScore olmalıdır, alınan tip: {type(self.score).__name__}")
        if not isinstance(self.threshold, (int, float)):
            raise AIConfidenceError(f"threshold sayısal olmalıdır, alınan tip: {type(self.threshold).__name__}")
        if isinstance(self.threshold, int):
            object.__setattr__(self, "threshold", float(self.threshold))
        if not (0.0 <= self.threshold <= 1.0):
            raise AIConfidenceError(f"threshold 0.0-1.0 aralığında olmalıdır, alınan: {self.threshold}")

    @classmethod
    def create(
        cls,
        value: float,
        threshold: float | None = None,
    ) -> AIConfidence:
        """Yeni AIConfidence oluşturur.

        Args:
            value: Güven skoru (0.0-1.0).
            threshold: Expert review eşiği (varsayılan: 0.75).
        """
        return cls(
            score=ConfidenceScore(value=value),
            threshold=threshold if threshold is not None else cls.DEFAULT_EXPERT_REVIEW_THRESHOLD,
        )

    @property
    def value(self) -> float:
        """Güven skoru float değeri."""
        return self.score.value

    @property
    def requires_expert_review(self) -> bool:
        """Skor, eşiğin altında mı? (KR-019: expert review tetiklenir)."""
        return self.score.value < self.threshold

    @property
    def is_confident(self) -> bool:
        """Skor, eşiğe eşit veya üzerinde mi?"""
        return self.score.value >= self.threshold

    def with_threshold(self, new_threshold: float) -> AIConfidence:
        """Farklı eşikle yeni AIConfidence döner (immutable)."""
        return AIConfidence(score=self.score, threshold=new_threshold)

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "score": self.score.value,
            "threshold": self.threshold,
            "requires_expert_review": self.requires_expert_review,
        }

    def __repr__(self) -> str:
        return (
            f"AIConfidence(score={self.score.value}, "
            f"threshold={self.threshold}, "
            f"requires_expert_review={self.requires_expert_review})"
        )
