# PATH: src/infrastructure/external/weather_api_adapter.py
# DESC: Hava durumu API adapter'ı.
"""
Weather API adapter: hava durumu sağlayıcısı HTTP implementasyonu.

Uçuş uygunluğu kontrolü için hava durumu verisi sorgular.
KR-015-5: Hava durumu engeli, görev planlamasını etkiler.

Retry: Transient hatalarda exponential backoff.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class WeatherData:
    """Hava durumu veri nesnesi."""

    def __init__(
        self,
        *,
        latitude: float,
        longitude: float,
        timestamp: datetime,
        temperature_celsius: float,
        wind_speed_ms: float,
        precipitation_mm: float,
        cloud_cover_pct: float,
        visibility_km: float,
        conditions: str,
        raw_data: Optional[dict[str, Any]] = None,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = timestamp
        self.temperature_celsius = temperature_celsius
        self.wind_speed_ms = wind_speed_ms
        self.precipitation_mm = precipitation_mm
        self.cloud_cover_pct = cloud_cover_pct
        self.visibility_km = visibility_km
        self.conditions = conditions
        self.raw_data = raw_data or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat(),
            "temperature_celsius": self.temperature_celsius,
            "wind_speed_ms": self.wind_speed_ms,
            "precipitation_mm": self.precipitation_mm,
            "cloud_cover_pct": self.cloud_cover_pct,
            "visibility_km": self.visibility_km,
            "conditions": self.conditions,
        }


class WeatherAPIAdapter:
    """Hava durumu API adapter'ı.

    httpx async HTTP client ile weather provider'a bağlanır.
    Tüm sorgularda retry uygulanır.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.weather_api_url
        self._timeout = httpx.Timeout(settings.weather_timeout_seconds)
        self._api_key = settings.weather_api_key.get_secret_value()

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={"Accept": "application/json"},
        )

    @_RETRY_DECORATOR
    async def get_current_weather(
        self,
        *,
        latitude: float,
        longitude: float,
    ) -> WeatherData:
        """Belirtilen konum için güncel hava durumunu sorgula."""
        logger.info(
            "weather_request",
            latitude=latitude,
            longitude=longitude,
        )

        async with self._get_client() as client:
            response = await client.get(
                "/current",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self._api_key,
                    "units": "metric",
                },
            )
            response.raise_for_status()
            data = response.json()

        weather = WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.utcnow(),
            temperature_celsius=data.get("main", {}).get("temp", 0.0),
            wind_speed_ms=data.get("wind", {}).get("speed", 0.0),
            precipitation_mm=data.get("rain", {}).get("1h", 0.0),
            cloud_cover_pct=data.get("clouds", {}).get("all", 0.0),
            visibility_km=data.get("visibility", 10000) / 1000.0,
            conditions=data.get("weather", [{}])[0].get("main", "Unknown"),
            raw_data=data,
        )

        logger.info(
            "weather_result",
            conditions=weather.conditions,
            wind_speed_ms=weather.wind_speed_ms,
            precipitation_mm=weather.precipitation_mm,
        )
        return weather

    @_RETRY_DECORATOR
    async def get_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        hours_ahead: int = 24,
    ) -> list[WeatherData]:
        """Belirtilen konum için hava durumu tahminini sorgula."""
        logger.info(
            "weather_forecast_request",
            latitude=latitude,
            longitude=longitude,
            hours_ahead=hours_ahead,
        )

        async with self._get_client() as client:
            response = await client.get(
                "/forecast",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self._api_key,
                    "units": "metric",
                    "cnt": max(1, hours_ahead // 3),
                },
            )
            response.raise_for_status()
            data = response.json()

        forecasts: list[WeatherData] = []
        for item in data.get("list", []):
            dt = datetime.utcfromtimestamp(item.get("dt", 0))
            forecasts.append(
                WeatherData(
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=dt,
                    temperature_celsius=item.get("main", {}).get("temp", 0.0),
                    wind_speed_ms=item.get("wind", {}).get("speed", 0.0),
                    precipitation_mm=item.get("rain", {}).get("3h", 0.0),
                    cloud_cover_pct=item.get("clouds", {}).get("all", 0.0),
                    visibility_km=item.get("visibility", 10000) / 1000.0,
                    conditions=item.get("weather", [{}])[0].get("main", "Unknown"),
                    raw_data=item,
                )
            )

        return forecasts

    async def health_check(self) -> bool:
        """Weather API erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get(
                    "/current",
                    params={
                        "lat": 39.9334,
                        "lon": 32.8597,
                        "appid": self._api_key,
                        "units": "metric",
                    },
                )
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("weather_health_check_failed")
            return False
