# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Weather block reporting and validation endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/weather-block-reports", tags=["weather-block-reports"])


class WeatherBlockReportCreateRequest(BaseModel):
    weather_block_id: str = Field(min_length=3, max_length=64)
    report_type: str = Field(min_length=3, max_length=32)
    details: str | None = Field(default=None, max_length=500)


class WeatherBlockReportResponse(BaseModel):
    report_id: str
    weather_block_id: str
    report_type: str
    created_at: datetime


class WeatherBlockReportService(Protocol):
    def create(self, payload: WeatherBlockReportCreateRequest, actor_subject: str) -> WeatherBlockReportResponse: ...


@dataclass(slots=True)
class _InMemoryWeatherBlockReportService:
    def create(self, payload: WeatherBlockReportCreateRequest, actor_subject: str) -> WeatherBlockReportResponse:
        _ = actor_subject
        return WeatherBlockReportResponse(
            report_id="wbr-1",
            weather_block_id=payload.weather_block_id,
            report_type=payload.report_type,
            created_at=datetime.utcnow(),
        )


def get_weather_block_report_service() -> WeatherBlockReportService:
    return _InMemoryWeatherBlockReportService()


def _require_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return str(getattr(user, "subject", ""))


@router.post("", response_model=WeatherBlockReportResponse, status_code=status.HTTP_201_CREATED)
def create_weather_block_report(
    request: Request,
    payload: WeatherBlockReportCreateRequest,
    service: WeatherBlockReportService = Depends(get_weather_block_report_service),
) -> WeatherBlockReportResponse:
    subject = _require_subject(request)
    return service.create(payload=payload, actor_subject=subject)
