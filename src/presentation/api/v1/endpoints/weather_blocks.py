# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Weather block query endpoints.
"""Weather block query endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/weather-blocks", tags=["weather-blocks"])


class WeatherBlockDTO(BaseModel):
    weather_block_id: str
    starts_at: datetime
    ends_at: datetime
    severity: str


class WeatherBlockListResponse(BaseModel):
    items: list[WeatherBlockDTO]


class WeatherBlockService(Protocol):
    def list_for_field(self, field_id: str, limit: int) -> WeatherBlockListResponse: ...


@dataclass(slots=True)
class _InMemoryWeatherBlockService:
    def list_for_field(self, field_id: str, limit: int) -> WeatherBlockListResponse:
        return WeatherBlockListResponse(
            items=[
                WeatherBlockDTO(
                    weather_block_id=f"wb-{field_id}",
                    starts_at=datetime.utcnow(),
                    ends_at=datetime.utcnow(),
                    severity="medium",
                )
            ][:limit]
        )


def get_weather_block_service(request: Request) -> WeatherBlockService:
    services = getattr(request.app.state, "services", None)
    if services is not None:
        svc = services.get("weather_block_service")
        if svc is not None:
            return cast(WeatherBlockService, svc)
    return _InMemoryWeatherBlockService()


def _require_subject(request: Request) -> None:
    if getattr(request.state, "user", None) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.get("", response_model=WeatherBlockListResponse)
def list_weather_blocks(
    request: Request,
    field_id: str = Query(min_length=3, max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    service: WeatherBlockService = Depends(get_weather_block_service),
) -> WeatherBlockListResponse:
    _require_subject(request)
    return service.list_for_field(field_id=field_id, limit=limit)
