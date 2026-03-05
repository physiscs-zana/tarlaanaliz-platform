# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/services/weather_validator.py
# DESC: Pilot hava raporu kayıt ve analiz servisi (KR-015-3A, KR-015-5).
# KR-015-3A: Pilot hava kararında TEK OTORİTE. Sistem weather API override EDEMEZ.
#            "Rapor gönderildi = kabul" — doğrulama (rejection) fazı YOK.
#            validate() sadece kayıt/analiz amaçlı; sonuç ASLA uçuşu bloke etmez.

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class WeatherValidationError(Exception):
    """Hava raporu doğrulama domain invariant ihlali."""


class WeatherSeverity(Enum):
    """Hava koşulu şiddet seviyesi."""

    LOW = "low"  # Uçuş mümkün ama riskli
    MODERATE = "moderate"  # Uçuş önerilmez
    HIGH = "high"  # Uçuş kesinlikle yapılmamalı
    EXTREME = "extreme"  # Acil durum


class FlightRecommendation(Enum):
    """Uçuş önerisi."""

    CLEAR_TO_FLY = "clear_to_fly"  # Uçuş yapılabilir
    DELAY_RECOMMENDED = "delay_recommended"  # Erteleme önerilir
    NO_FLY = "no_fly"  # Uçuş yapılmamalı
    GROUND_ALL = "ground_all"  # Tüm uçuşlar iptal


# Geçerli hava koşulları
VALID_WEATHER_CONDITIONS: frozenset[str] = frozenset({
    "rain",
    "heavy_rain",
    "wind",
    "strong_wind",
    "cloud",
    "overcast",
    "fog",
    "hail",
    "snow",
    "storm",
    "dust",
    "clear",
})


@dataclass(frozen=True)
class WeatherData:
    """Hava durumu verisi."""

    condition: str  # rain, wind, cloud, fog, vb.
    wind_speed_kmh: float | None = None  # Rüzgar hızı (km/h)
    visibility_km: float | None = None  # Görüş mesafesi (km)
    precipitation_mm: float | None = None  # Yağış miktarı (mm)
    cloud_cover_percent: float | None = None  # Bulut örtüsü (%)
    temperature_celsius: float | None = None  # Sıcaklık (°C)


@dataclass(frozen=True)
class WeatherValidationResult:
    """Hava raporu doğrulama sonucu."""

    mission_id: uuid.UUID
    severity: WeatherSeverity
    recommendation: FlightRecommendation
    is_valid_report: bool
    conditions_met: tuple[str, ...]  # Karşılanan koşullar
    warnings: tuple[str, ...]
    validated_at: datetime


class WeatherValidator:
    """Pilot hava raporu doğrulama servisi (KR-015-5).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Hava koşulu bilinen bir tür olmalıdır.
    - Rüzgar hızı, görüş mesafesi vb. mantıklı aralıkta olmalıdır.
    - Şiddet seviyesine göre uçuş önerisi verilir.
    - Weather block force majeure olarak reschedule token tüketmez.
    """

    # Uçuş eşik değerleri
    MAX_WIND_SPEED_KMH: float = 40.0  # Üzerinde NO_FLY
    WIND_WARNING_KMH: float = 25.0  # Üzerinde uyarı
    MIN_VISIBILITY_KM: float = 1.5  # Altında NO_FLY
    VISIBILITY_WARNING_KM: float = 3.0  # Altında uyarı
    MAX_PRECIPITATION_MM: float = 5.0  # Üzerinde NO_FLY
    PRECIPITATION_WARNING_MM: float = 2.0  # Üzerinde uyarı
    MAX_CLOUD_COVER_PERCENT: float = 90.0  # Üzerinde uyarı (multispektral etkilenir)

    def validate(
        self,
        *,
        mission_id: uuid.UUID,
        weather_data: WeatherData,
    ) -> WeatherValidationResult:
        """Hava durumu verilerini KAYDEDİP analiz eder — ASLA bloke etmez.

        KR-015-3A: Bu metod SADECE kayıt ve bilgilendirme amaçlıdır.
        Pilot raporu gönderildiği anda otomatik olarak KABUL edilir.
        Sonuç (recommendation/severity) uçuşu engelleyemez; caller bu değeri
        yalnızca loglama, dashboard gösterimi ve istatistik amaçlı kullanmalıdır.

        Args:
            mission_id: Mission ID.
            weather_data: Hava durumu verisi.

        Returns:
            WeatherValidationResult: Analiz sonucu (bilgilendirme amaçlı).
        """
        conditions_met: list[str] = []
        warnings: list[str] = []
        severity = WeatherSeverity.LOW
        is_valid = True

        # Koşul doğrulama
        condition = weather_data.condition.strip().lower()
        if condition not in VALID_WEATHER_CONDITIONS:
            is_valid = False
            warnings.append(f"Bilinmeyen hava koşulu: {condition}")

        # Şiddetli koşul kontrolü
        if condition in ("storm", "hail", "heavy_rain"):
            severity = WeatherSeverity.EXTREME
            conditions_met.append(f"Şiddetli koşul: {condition}")
        elif condition in ("strong_wind", "snow"):
            severity = max(severity, WeatherSeverity.HIGH, key=_severity_rank)
            conditions_met.append(f"Yüksek şiddetli koşul: {condition}")
        elif condition in ("rain", "fog", "dust"):
            severity = max(severity, WeatherSeverity.MODERATE, key=_severity_rank)
            conditions_met.append(f"Orta şiddetli koşul: {condition}")

        # Rüzgar kontrolü
        if weather_data.wind_speed_kmh is not None:
            if weather_data.wind_speed_kmh < 0:
                is_valid = False
                warnings.append("Rüzgar hızı negatif olamaz.")
            elif weather_data.wind_speed_kmh > self.MAX_WIND_SPEED_KMH:
                severity = max(severity, WeatherSeverity.HIGH, key=_severity_rank)
                conditions_met.append(
                    f"Rüzgar hızı aşırı: {weather_data.wind_speed_kmh:.1f} km/h"
                )
            elif weather_data.wind_speed_kmh > self.WIND_WARNING_KMH:
                severity = max(severity, WeatherSeverity.MODERATE, key=_severity_rank)
                warnings.append(
                    f"Rüzgar hızı yüksek: {weather_data.wind_speed_kmh:.1f} km/h"
                )

        # Görüş mesafesi kontrolü
        if weather_data.visibility_km is not None:
            if weather_data.visibility_km < 0:
                is_valid = False
                warnings.append("Görüş mesafesi negatif olamaz.")
            elif weather_data.visibility_km < self.MIN_VISIBILITY_KM:
                severity = max(severity, WeatherSeverity.HIGH, key=_severity_rank)
                conditions_met.append(
                    f"Görüş mesafesi yetersiz: {weather_data.visibility_km:.1f} km"
                )
            elif weather_data.visibility_km < self.VISIBILITY_WARNING_KM:
                severity = max(severity, WeatherSeverity.MODERATE, key=_severity_rank)
                warnings.append(
                    f"Görüş mesafesi düşük: {weather_data.visibility_km:.1f} km"
                )

        # Yağış kontrolü
        if weather_data.precipitation_mm is not None:
            if weather_data.precipitation_mm < 0:
                is_valid = False
                warnings.append("Yağış miktarı negatif olamaz.")
            elif weather_data.precipitation_mm > self.MAX_PRECIPITATION_MM:
                severity = max(severity, WeatherSeverity.HIGH, key=_severity_rank)
                conditions_met.append(
                    f"Yağış miktarı aşırı: {weather_data.precipitation_mm:.1f} mm"
                )
            elif weather_data.precipitation_mm > self.PRECIPITATION_WARNING_MM:
                severity = max(severity, WeatherSeverity.MODERATE, key=_severity_rank)
                warnings.append(
                    f"Yağış miktarı yüksek: {weather_data.precipitation_mm:.1f} mm"
                )

        # Bulut örtüsü kontrolü (multispektral analiz kalitesini etkiler)
        if weather_data.cloud_cover_percent is not None:
            if not 0.0 <= weather_data.cloud_cover_percent <= 100.0:
                is_valid = False
                warnings.append("Bulut örtüsü %0-100 arasında olmalıdır.")
            elif weather_data.cloud_cover_percent > self.MAX_CLOUD_COVER_PERCENT:
                severity = max(severity, WeatherSeverity.MODERATE, key=_severity_rank)
                warnings.append(
                    f"Bulut örtüsü yüksek: %{weather_data.cloud_cover_percent:.0f} "
                    f"(multispektral analiz kalitesi düşebilir)."
                )

        # Uçuş önerisi belirleme
        recommendation = self._determine_recommendation(severity)

        return WeatherValidationResult(
            mission_id=mission_id,
            severity=severity,
            recommendation=recommendation,
            is_valid_report=is_valid,
            conditions_met=tuple(conditions_met),
            warnings=tuple(warnings),
            validated_at=datetime.now(timezone.utc),
        )

    def _determine_recommendation(
        self,
        severity: WeatherSeverity,
    ) -> FlightRecommendation:
        """Şiddet seviyesine göre uçuş önerisi belirler."""
        match severity:
            case WeatherSeverity.LOW:
                return FlightRecommendation.CLEAR_TO_FLY
            case WeatherSeverity.MODERATE:
                return FlightRecommendation.DELAY_RECOMMENDED
            case WeatherSeverity.HIGH:
                return FlightRecommendation.NO_FLY
            case WeatherSeverity.EXTREME:
                return FlightRecommendation.GROUND_ALL

    def is_force_majeure(self, result: WeatherValidationResult) -> bool:
        """Force majeure (mücbir sebep) olup olmadığını belirler.

        Force majeure durumunda reschedule token tüketilmez (KR-015-5).
        """
        return result.severity in (WeatherSeverity.HIGH, WeatherSeverity.EXTREME)

    def should_block_mission(self, result: WeatherValidationResult) -> bool:
        """Mission'ın engellenmesi gerekip gerekmediğini belirler."""
        return result.recommendation in (
            FlightRecommendation.NO_FLY,
            FlightRecommendation.GROUND_ALL,
        )


def _severity_rank(severity: WeatherSeverity) -> int:
    """Şiddet seviyesi sıralama yardımcısı (max() için)."""
    return {
        WeatherSeverity.LOW: 0,
        WeatherSeverity.MODERATE: 1,
        WeatherSeverity.HIGH: 2,
        WeatherSeverity.EXTREME: 3,
    }.get(severity, 0)
