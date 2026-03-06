# PATH: src/core/domain/value_objects/recommended_action.py
# DESC: RecommendedAction VO; QC sonrası aksiyon önerisi (KR-082).
# SSOT: KR-018 (kalibrasyon hard gate), KR-082 (QC gate)
"""
RecommendedAction value object.

QC değerlendirme sonrası önerilen aksiyonu temsil eder.
KR-082 QC gate mekanizmasıyla uyumlu; QCStatus ile eşleşme kuralları içerir.
Entity katmanındaki QCRecommendedAction enum'u ile SSOT uyumludur;
bu VO domain genelinde taşınabilir referans noktasıdır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class RecommendedActionError(Exception):
    """RecommendedAction domain invariant ihlali."""


@dataclass(frozen=True)
class RecommendedAction:
    """QC sonrası önerilen aksiyon değer nesnesi (KR-082).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Aksiyonlar:
    - PROCEED: Analize devam et (QCStatus.PASS durumunda).
    - REVIEW: Manuel inceleme gerekli (QCStatus.WARN durumunda).
    - RETRY: Yeniden veri toplama gerekli (QCStatus.FAIL durumunda).
    - RECALIBRATE: Yeniden kalibrasyon gerekli (kalibrasyon hatası).
    - RECAPTURE: Yeniden görüntü çekimi gerekli (görüntü kalitesi sorunu).

    Invariants:
    - value, tanımlı geçerli aksiyonlardan biri olmalıdır.
    """

    value: str

    # Sabit aksiyon kodları
    PROCEED: ClassVar[str] = "PROCEED"
    REVIEW: ClassVar[str] = "REVIEW"
    RETRY: ClassVar[str] = "RETRY"
    RECALIBRATE: ClassVar[str] = "RECALIBRATE"
    RECAPTURE: ClassVar[str] = "RECAPTURE"

    _VALID_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "PROCEED",
            "REVIEW",
            "RETRY",
            "RECALIBRATE",
            "RECAPTURE",
        }
    )

    # Aksiyon -> Türkçe görünen ad eşlemesi
    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "PROCEED": "Devam Et",
        "REVIEW": "Manuel İnceleme",
        "RETRY": "Yeniden Dene",
        "RECALIBRATE": "Yeniden Kalibrasyon",
        "RECAPTURE": "Yeniden Çekim",
    }

    # Aksiyonlar arası öncelik (düşük sayı = yüksek öncelik / aciliyet)
    _PRIORITY: ClassVar[dict[str, int]] = {
        "RECAPTURE": 1,
        "RECALIBRATE": 2,
        "RETRY": 3,
        "REVIEW": 4,
        "PROCEED": 5,
    }

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise RecommendedActionError(f"value str olmalıdır, alınan tip: {type(self.value).__name__}")
        normalized = self.value.strip().upper()
        if normalized != self.value:
            object.__setattr__(self, "value", normalized)
        if self.value not in self._VALID_VALUES:
            raise RecommendedActionError(
                f"Geçersiz aksiyon: '{self.value}'. Geçerli değerler: {sorted(self._VALID_VALUES)}"
            )

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Türkçe görünen ad."""
        return self._DISPLAY_NAMES[self.value]

    @property
    def priority(self) -> int:
        """Aksiyon öncelik sırası (düşük = acil)."""
        return self._PRIORITY[self.value]

    @property
    def allows_analysis(self) -> bool:
        """Bu aksiyon analize devam etmeye izin veriyor mu? (KR-018 gate)."""
        return self.value in {self.PROCEED, self.REVIEW}

    @property
    def requires_human_intervention(self) -> bool:
        """Bu aksiyon insan müdahalesi gerektiriyor mu?"""
        return self.value in {self.REVIEW, self.RECALIBRATE, self.RECAPTURE}

    @property
    def is_blocking(self) -> bool:
        """Bu aksiyon analiz başlatmayı engelliyor mu? (KR-018 hard gate)."""
        return self.value in {self.RETRY, self.RECALIBRATE, self.RECAPTURE}

    def is_more_urgent_than(self, other: RecommendedAction) -> bool:
        """Bu aksiyon diğerinden daha acil mi?"""
        return self.priority < other.priority

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "value": self.value,
            "display_name": self.display_name,
            "allows_analysis": self.allows_analysis,
        }

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"RecommendedAction(value='{self.value}')"
