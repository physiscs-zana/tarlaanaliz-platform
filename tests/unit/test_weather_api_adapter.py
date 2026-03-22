# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-5: Open-Meteo WeatherAPIAdapter unit tests — WMO code mapping ve WeatherValidator.
"""Open-Meteo WeatherAPIAdapter unit tests — WMO code mapping and WeatherData."""

from __future__ import annotations

import pytest

from src.infrastructure.external.weather_api_adapter import (
    WeatherData,
    _wmo_code_to_condition,
)


@pytest.mark.unit
class TestWMOCodeMapping:
    """WMO weather code → condition string mapping tests."""

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            (0, "clear"),
            (1, "clear"),
            (2, "cloud"),
            (3, "overcast"),
            (45, "fog"),
            (48, "fog"),
            (61, "rain"),
            (65, "heavy_rain"),
            (71, "snow"),
            (95, "storm"),
            (96, "hail"),
            (99, "hail"),
            (999, "clear"),  # unknown code defaults to clear
        ],
    )
    def test_wmo_code_maps_to_correct_condition(self, code: int, expected: str) -> None:
        assert _wmo_code_to_condition(code) == expected


@pytest.mark.unit
class TestWeatherData:
    """WeatherData DTO tests."""

    def test_to_dict_returns_all_fields(self) -> None:
        from datetime import datetime, timezone

        wd = WeatherData(
            latitude=37.15,
            longitude=38.73,
            timestamp=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
            temperature_celsius=32.5,
            wind_speed_ms=4.2,
            precipitation_mm=0.0,
            cloud_cover_pct=15.0,
            visibility_km=10.0,
            conditions="clear",
        )
        d = wd.to_dict()
        assert d["latitude"] == 37.15
        assert d["longitude"] == 38.73
        assert d["temperature_celsius"] == 32.5
        assert d["wind_speed_ms"] == 4.2
        assert d["conditions"] == "clear"
        assert "timestamp" in d

    def test_raw_data_defaults_to_empty_dict(self) -> None:
        from datetime import datetime, timezone

        wd = WeatherData(
            latitude=0,
            longitude=0,
            timestamp=datetime.now(timezone.utc),
            temperature_celsius=0,
            wind_speed_ms=0,
            precipitation_mm=0,
            cloud_cover_pct=0,
            visibility_km=0,
            conditions="clear",
        )
        assert wd.raw_data == {}


@pytest.mark.unit
class TestWeatherValidator:
    """WeatherValidator domain service basic tests."""

    def test_clear_weather_returns_clear_to_fly(self) -> None:
        import uuid

        from src.core.domain.services.weather_validator import (
            FlightRecommendation,
            WeatherData as WVData,
            WeatherSeverity,
            WeatherValidator,
        )

        validator = WeatherValidator()
        result = validator.validate(
            mission_id=uuid.uuid4(),
            weather_data=WVData(
                condition="clear",
                wind_speed_kmh=10.0,
                visibility_km=10.0,
                precipitation_mm=0.0,
                cloud_cover_percent=5.0,
            ),
        )
        assert result.severity == WeatherSeverity.LOW
        assert result.recommendation == FlightRecommendation.CLEAR_TO_FLY
        assert result.is_valid_report is True

    def test_storm_returns_ground_all(self) -> None:
        import uuid

        from src.core.domain.services.weather_validator import (
            FlightRecommendation,
            WeatherData as WVData,
            WeatherSeverity,
            WeatherValidator,
        )

        validator = WeatherValidator()
        result = validator.validate(
            mission_id=uuid.uuid4(),
            weather_data=WVData(condition="storm"),
        )
        assert result.severity == WeatherSeverity.EXTREME
        assert result.recommendation == FlightRecommendation.GROUND_ALL

    def test_high_wind_returns_no_fly(self) -> None:
        import uuid

        from src.core.domain.services.weather_validator import (
            FlightRecommendation,
            WeatherData as WVData,
            WeatherValidator,
        )

        validator = WeatherValidator()
        result = validator.validate(
            mission_id=uuid.uuid4(),
            weather_data=WVData(condition="clear", wind_speed_kmh=50.0),
        )
        assert result.recommendation == FlightRecommendation.NO_FLY

    def test_force_majeure_for_extreme_weather(self) -> None:
        import uuid

        from src.core.domain.services.weather_validator import (
            WeatherData as WVData,
            WeatherValidator,
        )

        validator = WeatherValidator()
        result = validator.validate(
            mission_id=uuid.uuid4(),
            weather_data=WVData(condition="hail"),
        )
        assert validator.is_force_majeure(result) is True
        assert validator.should_block_mission(result) is True
