# PATH: src/core/domain/value_objects/confidence_score.py
# DESC: ConfidenceScore VO; model confidence değeri (0.0-1.0).

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConfidenceScoreError(Exception):
    """ConfidenceScore domain invariant ihlali."""


@dataclass(frozen=True)
class ConfidenceScore:
    """Model güven skoru (0.0-1.0 aralığında).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Kullanım alanları:
    - AnalysisResult finding confidence (KR-081)
    - Expert review confidence (KR-019)
    - Genel amaçlı güven skoru sarmalayıcı

    Invariants:
    - value, 0.0 ile 1.0 arasında olmalıdır (dahil).
    - value, sayısal (int veya float) olmalıdır.
    """

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise ConfidenceScoreError(f"value sayısal olmalıdır, alınan tip: {type(self.value).__name__}")
        # int ise float'a dönüştür (frozen bypass)
        if isinstance(self.value, int):
            object.__setattr__(self, "value", float(self.value))
        if not (0.0 <= self.value <= 1.0):
            raise ConfidenceScoreError(f"value 0.0-1.0 aralığında olmalıdır, alınan: {self.value}")

    def exceeds(self, threshold: float) -> bool:
        """Skor belirtilen eşiği aşıyor mu?"""
        return self.value > threshold

    def meets(self, threshold: float) -> bool:
        """Skor belirtilen eşiğe eşit veya üzerinde mi?"""
        return self.value >= threshold

    def is_low(self, threshold: float = 0.75) -> bool:
        """Skor düşük mü? (varsayılan eşik: 0.75, KR-019)."""
        return self.value < threshold

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {"value": self.value}

    def __float__(self) -> float:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConfidenceScore):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, ConfidenceScore):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, ConfidenceScore):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, ConfidenceScore):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, ConfidenceScore):
            return self.value >= other.value
        return NotImplemented

    def __repr__(self) -> str:
        return f"ConfidenceScore(value={self.value})"
