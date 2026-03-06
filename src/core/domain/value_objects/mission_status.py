# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/mission_status.py
# DESC: MissionStatus VO; durum enum ve geçiş kuralları (KR-028).

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class MissionStatusError(Exception):
    """MissionStatus domain invariant ihlali."""


@dataclass(frozen=True)
class MissionStatus:
    """Görev (Mission) durum değer nesnesi ve geçiş kuralları.

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Durum makinesi (KR-028, SSOT):
        PLANNED -> ASSIGNED -> ACKED -> FLOWN -> UPLOADED -> ANALYZING -> DONE
                                                                       -> FAILED
                                                                       -> CANCELLED
    Ayrıca: PLANNED -> CANCELLED, ASSIGNED -> CANCELLED, ACKED -> CANCELLED (erken iptal)

    Invariants:
    - value, tanımlı geçerli durumlardan biri olmalıdır.
    - Geçişler sadece _TRANSITIONS tablosundaki kurallara uygun olmalıdır.
    """

    value: str

    # Sabit durum değerleri
    PLANNED: ClassVar[str] = "PLANNED"
    ASSIGNED: ClassVar[str] = "ASSIGNED"
    ACKED: ClassVar[str] = "ACKED"
    FLOWN: ClassVar[str] = "FLOWN"
    UPLOADED: ClassVar[str] = "UPLOADED"
    ANALYZING: ClassVar[str] = "ANALYZING"
    DONE: ClassVar[str] = "DONE"
    FAILED: ClassVar[str] = "FAILED"
    CANCELLED: ClassVar[str] = "CANCELLED"

    _VALID_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "PLANNED",
            "ASSIGNED",
            "ACKED",
            "FLOWN",
            "UPLOADED",
            "ANALYZING",
            "DONE",
            "FAILED",
            "CANCELLED",
        }
    )

    _TRANSITIONS: ClassVar[dict[str, frozenset[str]]] = {
        "PLANNED": frozenset({"ASSIGNED", "FAILED", "CANCELLED"}),
        "ASSIGNED": frozenset({"ACKED", "FAILED", "CANCELLED"}),
        "ACKED": frozenset({"FLOWN", "FAILED", "CANCELLED"}),
        "FLOWN": frozenset({"UPLOADED", "FAILED", "CANCELLED"}),
        "UPLOADED": frozenset({"ANALYZING", "FAILED", "CANCELLED"}),
        "ANALYZING": frozenset({"DONE", "FAILED", "CANCELLED"}),
        "DONE": frozenset(),
        "FAILED": frozenset(),
        "CANCELLED": frozenset(),
    }

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise MissionStatusError(f"value str olmalıdır, alınan tip: {type(self.value).__name__}")
        normalized = self.value.strip().upper()
        if normalized != self.value:
            object.__setattr__(self, "value", normalized)
        if self.value not in self._VALID_VALUES:
            raise MissionStatusError(f"Geçersiz durum: '{self.value}'. Geçerli değerler: {sorted(self._VALID_VALUES)}")

    def can_transition_to(self, target: MissionStatus | str) -> bool:
        """Bu durumdan hedef duruma geçiş yapılabilir mi?"""
        target_value = target.value if isinstance(target, MissionStatus) else target
        allowed = self._TRANSITIONS.get(self.value, frozenset())
        return target_value in allowed

    def transition_to(self, target: MissionStatus | str) -> MissionStatus:
        """Hedef duruma geçiş yapar; geçersizse MissionStatusError fırlatır.

        Immutable olduğu için yeni bir MissionStatus döner.
        """
        target_value = target.value if isinstance(target, MissionStatus) else target
        if not self.can_transition_to(target_value):
            allowed = self._TRANSITIONS.get(self.value, frozenset())
            raise MissionStatusError(
                f"'{self.value}' -> '{target_value}' geçişi geçersiz. İzin verilen: {sorted(allowed)}"
            )
        return MissionStatus(value=target_value)

    @property
    def is_terminal(self) -> bool:
        """Durum terminal (son) durumda mı? (DONE, FAILED, CANCELLED)."""
        return len(self._TRANSITIONS.get(self.value, frozenset())) == 0

    @property
    def is_active(self) -> bool:
        """Durum aktif mi? (terminal olmayan)."""
        return not self.is_terminal

    @property
    def is_in_progress(self) -> bool:
        """Görev fiilen devam ediyor mu? (ASSIGNED-ANALYZING arası)."""
        return self.value in {"ASSIGNED", "ACKED", "FLOWN", "UPLOADED", "ANALYZING"}

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {"value": self.value}

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"MissionStatus(value='{self.value}')"
