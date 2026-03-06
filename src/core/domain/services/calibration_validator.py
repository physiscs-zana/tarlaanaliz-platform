# PATH: src/core/domain/services/calibration_validator.py
# DESC: Radyometrik kalibrasyon doğrulama (KR-018).

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class CalibrationValidationError(Exception):
    """Kalibrasyon doğrulama domain invariant ihlali."""


@dataclass(frozen=True)
class CalibrationCheckItem:
    """Tek bir kalibrasyon kontrol kalemi."""

    check_name: str
    expected_value: float
    actual_value: float
    tolerance: float
    passed: bool

    @property
    def deviation(self) -> float:
        """Beklenen değerden sapma oranı."""
        if self.expected_value == 0.0:
            return abs(self.actual_value)
        return abs(self.actual_value - self.expected_value) / abs(self.expected_value)


@dataclass(frozen=True)
class CalibrationValidationResult:
    """Kalibrasyon doğrulama sonucu.

    qc_result: PASS | WARN | FAIL
    KR-018: FAIL durumunda AnalysisJob başlatılamaz (hard gate).
    """

    mission_id: uuid.UUID
    batch_id: uuid.UUID
    qc_result: str  # PASS | WARN | FAIL
    checks: tuple[CalibrationCheckItem, ...]
    issues: tuple[str, ...]
    validated_at: datetime

    @property
    def is_passed(self) -> bool:
        return self.qc_result == "PASS"

    @property
    def is_warning(self) -> bool:
        return self.qc_result == "WARN"

    @property
    def is_failed(self) -> bool:
        return self.qc_result == "FAIL"

    @property
    def allows_analysis(self) -> bool:
        """KR-018 hard gate: sadece PASS ve WARN analiz başlatabilir."""
        return self.qc_result in ("PASS", "WARN")


class CalibrationValidator:
    """Radyometrik kalibrasyon doğrulama servisi (KR-018).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.
    KR-018 hard gate: calibrated/QC kanıtı olmadan AnalysisJob başlatılmamalıdır.

    Domain invariants:
    - Referans panel okumaları belirli tolerans aralığında olmalıdır.
    - Sensör sıcaklık sapması kabul edilebilir sınırlar içinde olmalıdır.
    - Karanlık akım (dark current) okuması eşik değerinin altında olmalıdır.
    - En az bir referans panel okuma gereklidir.
    - Tüm kontroller geçmezse FAIL; bazıları uyarı veriyorsa WARN; hepsi geçerse PASS.
    """

    # Varsayılan eşik değerleri
    DEFAULT_PANEL_REFLECTANCE_TOLERANCE: float = 0.05  # %5 sapma toleransı
    DEFAULT_DARK_CURRENT_MAX: float = 50.0  # Maksimum dark current değeri
    DEFAULT_SENSOR_TEMP_TOLERANCE: float = 5.0  # Derece Celsius

    def __init__(
        self,
        panel_reflectance_tolerance: float | None = None,
        dark_current_max: float | None = None,
        sensor_temp_tolerance: float | None = None,
    ) -> None:
        self._panel_tolerance = (
            panel_reflectance_tolerance
            if panel_reflectance_tolerance is not None
            else self.DEFAULT_PANEL_REFLECTANCE_TOLERANCE
        )
        self._dark_current_max = dark_current_max if dark_current_max is not None else self.DEFAULT_DARK_CURRENT_MAX
        self._sensor_temp_tolerance = (
            sensor_temp_tolerance if sensor_temp_tolerance is not None else self.DEFAULT_SENSOR_TEMP_TOLERANCE
        )

    def validate(
        self,
        *,
        mission_id: uuid.UUID,
        batch_id: uuid.UUID,
        panel_readings: list[tuple[str, float, float]],
        dark_current_value: float | None = None,
        sensor_temperature: float | None = None,
        expected_sensor_temperature: float = 25.0,
    ) -> CalibrationValidationResult:
        """Kalibrasyon verilerini doğrular.

        Args:
            mission_id: İlgili mission ID.
            batch_id: Veri batch ID.
            panel_readings: (band_adı, beklenen_reflectance, okunan_reflectance) listesi.
            dark_current_value: Karanlık akım okuması (opsiyonel).
            sensor_temperature: Sensör sıcaklığı (opsiyonel).
            expected_sensor_temperature: Beklenen sensör sıcaklığı.

        Returns:
            CalibrationValidationResult: Doğrulama sonucu.

        Raises:
            CalibrationValidationError: Panel okuması yoksa.
        """
        if not panel_readings:
            raise CalibrationValidationError("En az bir referans panel okuması gereklidir.")

        checks: list[CalibrationCheckItem] = []
        issues: list[str] = []
        has_failure = False
        has_warning = False

        # Panel reflectance kontrolleri
        for band_name, expected, actual in panel_readings:
            tolerance = self._panel_tolerance
            deviation = abs(actual - expected) / abs(expected) if expected != 0.0 else abs(actual)
            passed = deviation <= tolerance
            warning_zone = tolerance < deviation <= tolerance * 2

            check = CalibrationCheckItem(
                check_name=f"panel_reflectance_{band_name}",
                expected_value=expected,
                actual_value=actual,
                tolerance=tolerance,
                passed=passed or warning_zone,
            )
            checks.append(check)

            if not passed and not warning_zone:
                has_failure = True
                issues.append(f"Band {band_name}: reflectance sapması {deviation:.4f} tolerans {tolerance:.4f} aşıldı.")
            elif warning_zone:
                has_warning = True
                issues.append(
                    f"Band {band_name}: reflectance sapması {deviation:.4f} "
                    f"uyarı bölgesinde (tolerans: {tolerance:.4f})."
                )

        # Dark current kontrolü
        if dark_current_value is not None:
            dc_passed = dark_current_value <= self._dark_current_max
            dc_warning = self._dark_current_max < dark_current_value <= self._dark_current_max * 1.5
            checks.append(
                CalibrationCheckItem(
                    check_name="dark_current",
                    expected_value=0.0,
                    actual_value=dark_current_value,
                    tolerance=self._dark_current_max,
                    passed=dc_passed or dc_warning,
                )
            )
            if not dc_passed and not dc_warning:
                has_failure = True
                issues.append(f"Dark current {dark_current_value:.2f} maksimum {self._dark_current_max:.2f} aşıldı.")
            elif dc_warning:
                has_warning = True
                issues.append(f"Dark current {dark_current_value:.2f} uyarı bölgesinde.")

        # Sensör sıcaklığı kontrolü
        if sensor_temperature is not None:
            temp_deviation = abs(sensor_temperature - expected_sensor_temperature)
            temp_passed = temp_deviation <= self._sensor_temp_tolerance
            temp_warning = self._sensor_temp_tolerance < temp_deviation <= self._sensor_temp_tolerance * 1.5
            checks.append(
                CalibrationCheckItem(
                    check_name="sensor_temperature",
                    expected_value=expected_sensor_temperature,
                    actual_value=sensor_temperature,
                    tolerance=self._sensor_temp_tolerance,
                    passed=temp_passed or temp_warning,
                )
            )
            if not temp_passed and not temp_warning:
                has_failure = True
                issues.append(
                    f"Sensör sıcaklık sapması {temp_deviation:.2f}°C "
                    f"tolerans {self._sensor_temp_tolerance:.2f}°C aşıldı."
                )
            elif temp_warning:
                has_warning = True
                issues.append(f"Sensör sıcaklık sapması {temp_deviation:.2f}°C uyarı bölgesinde.")

        # Sonuç belirleme
        if has_failure:
            qc_result = "FAIL"
        elif has_warning:
            qc_result = "WARN"
        else:
            qc_result = "PASS"

        return CalibrationValidationResult(
            mission_id=mission_id,
            batch_id=batch_id,
            qc_result=qc_result,
            checks=tuple(checks),
            issues=tuple(issues),
            validated_at=datetime.now(timezone.utc),
        )

    def can_start_analysis(self, result: CalibrationValidationResult) -> bool:
        """KR-018 hard gate: analiz başlatılabilir mi?

        FAIL durumunda kesinlikle başlatılamaz.
        PASS ve WARN durumunda başlatılabilir.
        """
        return result.allows_analysis
