# PATH: src/core/domain/value_objects/training_grade.py
# DESC: TrainingGrade VO; training veri kalite derecesi.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-019 (expert review), KR-081 (contract-first)
"""
TrainingGrade value object.

Uzman incelemesi (expert review) sonrası verilen training veri
kalite derecesini temsil eder. AI modeli eğitim veri setine
dahil edilecek verilerin kalitesini derecelendirir.
KR-019: Uzman incelemesi sonucu training feedback.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class TrainingGradeError(Exception):
    """TrainingGrade domain invariant ihlali."""


@dataclass(frozen=True)
class TrainingGrade:
    """Training veri kalite derecesi değer nesnesi (KR-019).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Kalite dereceleri (KR-019 v1.2.0):
    - A: En yüksek kalite; doğrulanmış ve güvenilir training verisi.
    - B: İyi kalite; küçük düzeltmelerle kullanılabilir.
    - C: Kabul edilebilir kalite; dikkatle kullanılmalı.
    - D: Düşük kalite; sınırlı kullanım.
    - REJECT: Reddedildi; training veri setine dahil edilemez.

    Invariants:
    - value, tanımlı geçerli derecelerden biri olmalıdır.
    """

    value: str

    # Sabit derece kodları (KR-019 v1.2.0)
    A: ClassVar[str] = "A"
    B: ClassVar[str] = "B"
    C: ClassVar[str] = "C"
    D: ClassVar[str] = "D"
    REJECT: ClassVar[str] = "REJECT"

    _VALID_VALUES: ClassVar[frozenset[str]] = frozenset({
        "A", "B", "C", "D", "REJECT",
    })

    # Derece -> Türkçe görünen ad eşlemesi
    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "A": "A (En Yüksek)",
        "B": "B (İyi)",
        "C": "C (Kabul Edilebilir)",
        "D": "D (Düşük)",
        "REJECT": "Reddedildi",
    }

    # Kalite sıralaması (yüksek sayı = yüksek kalite)
    _QUALITY_ORDER: ClassVar[dict[str, int]] = {
        "REJECT": 0,
        "D": 1,
        "C": 2,
        "B": 3,
        "A": 4,
    }

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TrainingGradeError(
                f"value str olmalıdır, alınan tip: {type(self.value).__name__}"
            )
        normalized = self.value.strip().upper()
        if normalized != self.value:
            object.__setattr__(self, "value", normalized)
        if self.value not in self._VALID_VALUES:
            raise TrainingGradeError(
                f"Geçersiz derece: '{self.value}'. "
                f"Geçerli değerler: {sorted(self._VALID_VALUES)}"
            )

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Türkçe görünen ad."""
        return self._DISPLAY_NAMES[self.value]

    @property
    def quality_score(self) -> int:
        """Kalite sıralaması (0-4 arası)."""
        return self._QUALITY_ORDER[self.value]

    @property
    def is_usable(self) -> bool:
        """Training veri setine dahil edilebilir mi?"""
        return self.value in {self.A, self.B, self.C, self.D}

    @property
    def is_high_quality(self) -> bool:
        """Yüksek kaliteli mi? (A veya B)."""
        return self.value in {self.A, self.B}

    @property
    def is_rejected(self) -> bool:
        """Reddedilmiş mi?"""
        return self.value == self.REJECT

    def is_better_than(self, other: TrainingGrade) -> bool:
        """Bu derece diğerinden daha iyi mi?"""
        return self.quality_score > other.quality_score

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "value": self.value,
            "display_name": self.display_name,
            "is_usable": self.is_usable,
        }

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TrainingGrade(value='{self.value}')"
