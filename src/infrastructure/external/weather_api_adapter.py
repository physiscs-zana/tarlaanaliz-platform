# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-5: Open-Meteo hava durumu API adapter'ı.
"""
Weather API adapter: Open-Meteo üzerinden hava durumu sorgusu.

Uçuş uygunluğu kontrolü ve görev planlama için hava durumu verisi sorgular.
KR-015-5: Hava durumu engeli, görev planlamasını etkiler.

Open-Meteo API:
- API key gerektirmez — sadece lat/lon gönderilir, PII sıfır.
- WMO weather code standardını kullanır.
- Tarımsal veriler desteklenir (toprak nemi, evapotranspirasyon).

Retry: Transient hatalarda exponential backoff.
"""

from __future__ import annotations

from datetime import datetime, timezone
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

# -------------------------------------------------------------------------
# WMO Weather Code → Condition string mapping
# https://open-meteo.com/en/docs  (WMO Weather interpretation codes)
# -------------------------------------------------------------------------
_WMO_CODE_TO_CONDITION: dict[int, str] = {
    0: "clear",
    1: "clear",         # Mainly clear
    2: "cloud",         # Partly cloudy
    3: "overcast",      # Overcast
    45: "fog",
    48: "fog",          # Depositing rime fog
    51: "rain",         # Drizzle: light
    53: "rain",         # Drizzle: moderate
    55: "rain",         # Drizzle: dense
    56: "rain",         # Freezing drizzle: light
    57: "rain",         # Freezing drizzle: dense
    61: "rain",         # Rain: slight
    63: "rain",         # Rain: moderate
    65: "heavy_rain",   # Rain: heavy
    66: "rain",         # Freezing rain: light
    67: "heavy_rain",   # Freezing rain: heavy
    71: "snow",         # Snow: slight
    73: "snow",         # Snow: moderate
    75: "snow",         # Snow: heavy
    77: "snow",         # Snow grains
    80: "rain",         # Rain showers: slight
    81: "rain",         # Rain showers: moderate
    82: "heavy_rain",   # Rain showers: violent
    85: "snow",         # Snow showers: slight
    86: "snow",         # Snow showers: heavy
    95: "storm",        # Thunderstorm
    96: "hail",         # Thunderstorm with slight hail
    99: "hail",         # Thunderstorm with heavy hail
}


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


def _wmo_code_to_condition(code: int) -> str:
    """WMO weather code → condition string."""
    return _WMO_CODE_TO_CONDITION.get(code, "clear")


class WeatherAPIAdapter:
    """Open-Meteo hava durumu API adapter'ı (KR-015-5).

    Sadece lat/lon gönderilir — API key yok, kullanıcı verisi yok,
    platform kimliği yok. Sızıntı riski sıfır.
    """

    # Open-Meteo parametreleri
    _CURRENT_PARAMS = (
        "temperature_2m,relative_humidity_2m,precipitation,rain,"
        "weather_code,cloud_cover,wind_speed_10m,wind_gusts_10m"
    )
    _HOURLY_PARAMS = (
        "temperature_2m,precipitation,rain,weather_code,cloud_cover,"
        "visibility,wind_speed_10m,wind_gusts_10m,"
        "soil_moisture_0_to_7cm,et0_fao_evapotranspiration"
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.weather_api_url or "https://api.open-meteo.com"
        self._timeout = httpx.Timeout(settings.weather_timeout_seconds)

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
        """Belirtilen konum için güncel hava durumunu sorgula.

        Open-Meteo /v1/forecast?current=... endpoint'ini kullanır.
        """
        logger.info("weather_request", latitude=latitude, longitude=longitude)

        async with self._get_client() as client:
            response = await client.get(
                "/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": self._CURRENT_PARAMS,
                    "timezone": "auto",
                },
            )
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})
        wmo_code = current.get("weather_code", 0)

        # Open-Meteo wind_speed_10m: km/h → m/s dönüşümü
        wind_kmh = current.get("wind_speed_10m", 0.0)
        wind_ms = wind_kmh / 3.6

        weather = WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(timezone.utc),
            temperature_celsius=current.get("temperature_2m", 0.0),
            wind_speed_ms=round(wind_ms, 2),
            precipitation_mm=current.get("precipitation", 0.0),
            cloud_cover_pct=current.get("cloud_cover", 0.0),
            visibility_km=10.0,  # Open-Meteo current endpoint'te visibility yok, hourly'den alınır
            conditions=_wmo_code_to_condition(wmo_code),
            raw_data=data,
        )

        logger.info(
            "weather_result",
            conditions=weather.conditions,
            wind_speed_ms=weather.wind_speed_ms,
            precipitation_mm=weather.precipitation_mm,
            cloud_cover_pct=weather.cloud_cover_pct,
        )
        return weather

    @_RETRY_DECORATOR
    async def get_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        hours_ahead: int = 72,
    ) -> list[WeatherData]:
        """Belirtilen konum için saatlik hava durumu tahmini.

        Open-Meteo /v1/forecast?hourly=... endpoint'ini kullanır.
        Tarımsal veriler de dahildir (toprak nemi, evapotranspirasyon).
        """
        logger.info(
            "weather_forecast_request",
            latitude=latitude,
            longitude=longitude,
            hours_ahead=hours_ahead,
        )
        forecast_days = max(1, min(hours_ahead // 24 + 1, 7))

        async with self._get_client() as client:
            response = await client.get(
                "/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": self._HOURLY_PARAMS,
                    "forecast_days": forecast_days,
                    "timezone": "auto",
                },
            )
            response.raise_for_status()
            data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        precips = hourly.get("precipitation", [])
        codes = hourly.get("weather_code", [])
        clouds = hourly.get("cloud_cover", [])
        visibilities = hourly.get("visibility", [])
        winds = hourly.get("wind_speed_10m", [])

        forecasts: list[WeatherData] = []
        for i, time_str in enumerate(times[:hours_ahead]):
            dt = datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)
            wind_kmh = winds[i] if i < len(winds) else 0.0
            vis_m = visibilities[i] if i < len(visibilities) else 10000.0
            wmo_code = codes[i] if i < len(codes) else 0

            forecasts.append(
                WeatherData(
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=dt,
                    temperature_celsius=temps[i] if i < len(temps) else 0.0,
                    wind_speed_ms=round(wind_kmh / 3.6, 2),
                    precipitation_mm=precips[i] if i < len(precips) else 0.0,
                    cloud_cover_pct=clouds[i] if i < len(clouds) else 0.0,
                    visibility_km=round(vis_m / 1000.0, 2) if vis_m else 10.0,
                    conditions=_wmo_code_to_condition(wmo_code),
                    raw_data={
                        "soil_moisture_0_to_7cm": (
                            hourly.get("soil_moisture_0_to_7cm", [None] * (i + 1))[i]
                        ),
                        "et0_fao_evapotranspiration": (
                            hourly.get("et0_fao_evapotranspiration", [None] * (i + 1))[i]
                        ),
                    },
                )
            )

        logger.info("weather_forecast_result", total_hours=len(forecasts))
        return forecasts

    async def get_flight_weather(
        self,
        *,
        latitude: float,
        longitude: float,
        target_date: str,
    ) -> list[WeatherData]:
        """Belirli bir gün için uçuş saatlerindeki (06:00-18:00) hava durumu.

        Görev planlama servisi bu metodu kullanarak uçuş günü uygunluğunu kontrol eder.

        Args:
            latitude: Tarla enlem.
            longitude: Tarla boylam.
            target_date: Hedef tarih (YYYY-MM-DD formatı).

        Returns:
            06:00-18:00 arası saatlik WeatherData listesi.
        """
        forecasts = await self.get_forecast(
            latitude=latitude, longitude=longitude, hours_ahead=168
        )

        # Hedef gün, 06:00-18:00 arası filtrele
        flight_hours: list[WeatherData] = []
        for f in forecasts:
            date_str = f.timestamp.strftime("%Y-%m-%d")
            if date_str == target_date and 6 <= f.timestamp.hour <= 18:
                flight_hours.append(f)

        return flight_hours

    async def health_check(self) -> bool:
        """Open-Meteo API erişilebilirliğini kontrol et.

        Ankara koordinatları ile basit sorgu — PII içermez.
        """
        try:
            async with self._get_client() as client:
                response = await client.get(
                    "/v1/forecast",
                    params={
                        "latitude": 39.93,
                        "longitude": 32.86,
                        "current": "temperature_2m",
                    },
                )
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("weather_health_check_failed")
            return False
