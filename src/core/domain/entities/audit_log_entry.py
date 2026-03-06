# PATH: src/core/domain/entities/audit_log_entry.py
# DESC: Append-only (WORM) audit log kaydi.
# SSOT: BOLUM 3 (gozlemlenebilirlik standardi), KR-062 (denetlenebilirlik)
"""
AuditLogEntry domain entity (immutable / frozen).

WORM (Write Once Read Many) / append-only audit log kaydi.
PII minimizasyonu: loglar PII ICERMEZ; actor_id_hash tek-yonlu kimliktir (BOLUM 3).
correlation_id HER ZAMAN zorunlu ve tum servislerde aynen tasinir.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


# BOLUM 3 kanonik enum degerleri
_VALID_EVENT_TYPES = frozenset(
    {
        "INGEST",
        "AUTH",
        "RBAC",
        "PRICING",
        "JOB",
        "RESULT",
        "SECURITY",
        "SYSTEM",
    }
)

_VALID_EVENT_ACTIONS = frozenset(
    {
        "CREATE",
        "VALIDATE",
        "UPLOAD",
        "QUEUE",
        "START",
        "FINISH",
        "DENY",
        "UPDATE",
    }
)

_VALID_OUTCOMES = frozenset({"SUCCESS", "FAIL"})

_VALID_ACTOR_TYPES = frozenset(
    {
        "farmer",
        "pilot",
        "il_operator",
        "admin",
        "system",
    }
)


@dataclass(frozen=True)
class AuditLogEntry:
    """Degismez (immutable) denetim log kaydi.

    * BOLUM 3 -- Log semasi + Correlation ID.
    * KR-062 -- Denetlenebilirlik: fiyat, kurum onayi, eslestirme, hakedis.
    * KR-066 -- PII minimizasyonu; actor_id_hash tek-yonlu hash.

    frozen=True: olusturulduktan sonra alanlari degistirilemez (WORM).
    """

    audit_log_id: uuid.UUID
    event_type: str  # INGEST|AUTH|RBAC|PRICING|JOB|RESULT|SECURITY|SYSTEM
    event_action: str  # CREATE|VALIDATE|UPLOAD|QUEUE|START|FINISH|DENY|UPDATE
    outcome: str  # SUCCESS|FAIL
    correlation_id: str  # corr_<hex> -- her zaman zorunlu
    actor_type: str  # farmer|pilot|il_operator|admin|system
    actor_id_hash: str  # hash of user_id, not direct PII
    created_at: datetime
    field_id: Optional[uuid.UUID] = None
    mission_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None
    card_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[uuid.UUID] = None
    change_details: Optional[Dict[str, Any]] = None  # JSONB
    error_code: Optional[str] = None
    error_message: Optional[str] = None  # max 120 chars, PII yok
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        # frozen=True prevents assignment; validation only
        if self.event_type not in _VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: '{self.event_type}'. Must be one of: {sorted(_VALID_EVENT_TYPES)}")
        if self.event_action not in _VALID_EVENT_ACTIONS:
            raise ValueError(
                f"Invalid event_action: '{self.event_action}'. Must be one of: {sorted(_VALID_EVENT_ACTIONS)}"
            )
        if self.outcome not in _VALID_OUTCOMES:
            raise ValueError(f"Invalid outcome: '{self.outcome}'. Must be one of: {sorted(_VALID_OUTCOMES)}")
        if not self.correlation_id or not self.correlation_id.strip():
            raise ValueError("correlation_id is required and must be present in every log entry (BOLUM 3)")
        if self.actor_type not in _VALID_ACTOR_TYPES:
            raise ValueError(f"Invalid actor_type: '{self.actor_type}'. Must be one of: {sorted(_VALID_ACTOR_TYPES)}")
        if not self.actor_id_hash or not self.actor_id_hash.strip():
            raise ValueError("actor_id_hash is required (hash of user_id, not PII)")
        # error_message max 120 karakter, PII yok
        if self.error_message and len(self.error_message) > 120:
            raise ValueError(f"error_message must be at most 120 characters (BOLUM 3), got {len(self.error_message)}")
