# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Application DTOs for contract-first payload mapping."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class AnalysisLayerDTO:
    layer_key: str
    value_type: str
    value_uri: str


@dataclass(frozen=True, slots=True)
class AnalysisResultDTO:
    analysis_id: str
    mission_id: str
    field_id: str
    dataset_id: str
    status: str
    summary: str | None
    confidence_score: float | None
    calibration_certificate_id: str
    # KR-018: calibration is a hard-gate, value must be present for valid result payload.
    layers: tuple[AnalysisLayerDTO, ...]
    created_at: datetime
    completed_at: datetime | None
    # KR-018/KR-023 v1.2.0: Graceful Degradation + katmanli rapor
    report_tier: str = "TEMEL"  # TEMEL | GENISLETILMIS | KAPSAMLI
    band_class: str = ""  # BASIC_4BAND | EXTENDED_5BAND
    available_indices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # KR-018: calibration hard-gate.
        if not self.calibration_certificate_id:
            raise ValueError("calibration_certificate_id is required")
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at cannot be earlier than created_at")

    # KR-081: stable contract mapping surface.
    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "mission_id": self.mission_id,
            "field_id": self.field_id,
            "dataset_id": self.dataset_id,
            "status": self.status,
            "summary": self.summary,
            "confidence_score": self.confidence_score,
            "calibration_certificate_id": self.calibration_certificate_id,
            "layers": [
                {"layer_key": layer.layer_key, "value_type": layer.value_type, "value_uri": layer.value_uri}
                for layer in self.layers
            ],
            "created_at": _to_utc_iso(self.created_at),
            "completed_at": _optional_dt(self.completed_at),
            "report_tier": self.report_tier,
            "band_class": self.band_class,
            "available_indices": list(self.available_indices),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AnalysisResultDTO:
        return cls(
            analysis_id=str(payload["analysis_id"]),
            mission_id=str(payload["mission_id"]),
            field_id=str(payload["field_id"]),
            dataset_id=str(payload["dataset_id"]),
            status=str(payload["status"]),
            summary=None if payload.get("summary") is None else str(payload["summary"]),
            confidence_score=None if payload.get("confidence_score") is None else float(payload["confidence_score"]),
            calibration_certificate_id=str(payload["calibration_certificate_id"]),
            layers=tuple(
                AnalysisLayerDTO(
                    layer_key=str(item["layer_key"]),
                    value_type=str(item["value_type"]),
                    value_uri=str(item["value_uri"]),
                )
                for item in payload.get("layers", [])
            ),
            created_at=_parse_datetime(payload["created_at"]),
            completed_at=_parse_optional_datetime(payload.get("completed_at")),
            report_tier=str(payload.get("report_tier", "TEMEL")),
            band_class=str(payload.get("band_class", "")),
            available_indices=tuple(payload.get("available_indices", ())),
        )


def _to_utc_iso(value: datetime) -> str:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _optional_dt(value: datetime | None) -> str | None:
    return None if value is None else _to_utc_iso(value)


def _parse_optional_datetime(raw: Any) -> datetime | None:
    return None if raw is None else _parse_datetime(raw)


def _parse_datetime(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
