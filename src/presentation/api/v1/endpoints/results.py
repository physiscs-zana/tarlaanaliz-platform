# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-017: Analysis results endpoints.
"""Analysis results endpoints (layer list + summary)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/results", tags=["results"])


class ResultLayerDTO(BaseModel):
    layer_name: str
    layer_type: str = ""  # v1.2.0: HEALTH | DISEASE | THERMAL_STRESS | ...
    uri: str


class ResultSummaryDTO(BaseModel):
    analysis_job_id: str
    mission_id: str
    layers: list[ResultLayerDTO]
    quality_status: str = Field(default="ready")
    # KR-018/KR-023 v1.2.0: Graceful Degradation + katmanli rapor
    report_tier: str = Field(default="TEMEL")  # TEMEL | GENISLETILMIS | KAPSAMLI
    band_class: str = Field(default="")  # BASIC_4BAND | EXTENDED_5BAND
    available_indices: list[str] = Field(default_factory=list)


class ResultsService(Protocol):
    def get_summary(self, analysis_job_id: str, actor_subject: str) -> ResultSummaryDTO: ...


@dataclass(slots=True)
class _InMemoryResultsService:
    def get_summary(self, analysis_job_id: str, actor_subject: str) -> ResultSummaryDTO:
        _ = actor_subject
        return ResultSummaryDTO(
            analysis_job_id=analysis_job_id,
            mission_id="msn-1",
            layers=[ResultLayerDTO(layer_name="ndvi", layer_type="HEALTH", uri="s3://demo/ndvi.tif")],
            report_tier="TEMEL",
            band_class="BASIC_4BAND",
            available_indices=["NDVI", "NDRE", "GNDVI"],
        )


def get_results_service(request: Request) -> ResultsService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("results_service")
        if svc is not None:
            return cast(ResultsService, svc)
    return _InMemoryResultsService()


def _require_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


@router.get("", response_model=list[ResultSummaryDTO])
def list_results(request: Request) -> list[ResultSummaryDTO]:
    """Return all analysis results. Empty until worker pipeline is running."""
    _require_subject(request)
    return []


@router.get("/{analysis_job_id}/summary", response_model=ResultSummaryDTO)
def get_result_summary(
    request: Request,
    analysis_job_id: str,
    service: ResultsService = Depends(get_results_service),
) -> ResultSummaryDTO:
    # KR-018: calibration hard-gate is enforced by application/domain prior to result publication.
    # SEC-FIX (M-04): Payment gate — ResultsService.get_summary() MUST verify that the
    # mission/analysis is PAID before returning layer URIs. When user_repo and payment
    # integration are wired, the service layer should check payment status and return
    # HTTP 402 if unpaid. Currently stub service has no real data, so gate is deferred
    # to the service implementation.
    subject = _require_subject(request)
    return service.get_summary(analysis_job_id=analysis_job_id, actor_subject=subject)
