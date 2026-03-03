# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/services/coverage_calculator.py
# DESC: Mission footprint ↔ field boundary kesişim hesabı (KR-016).

from __future__ import annotations

import uuid
from dataclasses import dataclass


class CoverageCalculationError(Exception):
    """Kapsam hesaplama domain invariant ihlali."""


@dataclass(frozen=True)
class Polygon:
    """Basit polygon temsili (kapalı halka).

    coordinates: ((lon, lat), ...) şeklinde tuple listesi.
    İlk ve son nokta aynı olmalıdır (kapalı polygon).
    En az 4 nokta (3 köşe + kapanış) gereklidir.
    """

    coordinates: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if len(self.coordinates) < 4:
            raise CoverageCalculationError(
                "Polygon en az 4 nokta içermelidir (3 köşe + kapanış)."
            )
        if self.coordinates[0] != self.coordinates[-1]:
            raise CoverageCalculationError(
                "Polygon kapalı olmalıdır (ilk ve son nokta aynı)."
            )


@dataclass(frozen=True)
class CoverageResult:
    """Kapsam hesaplama sonucu.

    coverage_ratio: Tarla alanının ne kadarının mission footprint ile
                    kesiştiğini gösterir (0.0 - 1.0).
    """

    mission_id: uuid.UUID
    field_id: uuid.UUID
    field_area_m2: float
    footprint_area_m2: float
    intersection_area_m2: float
    coverage_ratio: float  # 0.0 - 1.0
    is_sufficient: bool
    minimum_coverage_ratio: float


class CoverageCalculator:
    """Mission footprint ↔ field boundary kesişim hesabı servisi (KR-016).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Kapsam oranı 0.0 ile 1.0 arasında olmalıdır.
    - Minimum kapsam eşiği altındaki mission'lar yetersiz kabul edilir.
    - Alan hesaplamaları pozitif olmalıdır.

    Not: Gerçek geometrik kesişim hesabı için Shapely gibi bir kütüphane
    gerekir. Bu servis saf domain mantığını sağlar; karmaşık geometri
    hesaplamaları infrastructure katmanında yapılarak sonuçlar bu servise
    iletilir.
    """

    DEFAULT_MINIMUM_COVERAGE_RATIO: float = 0.80  # %80 minimum kapsam

    def __init__(
        self,
        minimum_coverage_ratio: float | None = None,
    ) -> None:
        self._min_coverage = (
            minimum_coverage_ratio
            if minimum_coverage_ratio is not None
            else self.DEFAULT_MINIMUM_COVERAGE_RATIO
        )
        if not 0.0 < self._min_coverage <= 1.0:
            raise CoverageCalculationError(
                "minimum_coverage_ratio 0.0 (exclusive) ile 1.0 arasında olmalıdır."
            )

    def evaluate_coverage(
        self,
        *,
        mission_id: uuid.UUID,
        field_id: uuid.UUID,
        field_area_m2: float,
        footprint_area_m2: float,
        intersection_area_m2: float,
    ) -> CoverageResult:
        """Önceden hesaplanmış alan değerleri ile kapsam değerlendirir.

        Infrastructure katmanı geometrik kesişim hesabını yapıp sonuçları
        bu metoda iletir.

        Args:
            mission_id: Mission ID.
            field_id: Tarla ID.
            field_area_m2: Tarla alanı (m²).
            footprint_area_m2: Mission footprint alanı (m²).
            intersection_area_m2: Kesişim alanı (m²).

        Returns:
            CoverageResult: Kapsam değerlendirme sonucu.

        Raises:
            CoverageCalculationError: Geçersiz alan değerleri.
        """
        if field_area_m2 <= 0:
            raise CoverageCalculationError("field_area_m2 pozitif olmalıdır.")
        if footprint_area_m2 < 0:
            raise CoverageCalculationError("footprint_area_m2 negatif olamaz.")
        if intersection_area_m2 < 0:
            raise CoverageCalculationError("intersection_area_m2 negatif olamaz.")
        if intersection_area_m2 > field_area_m2:
            raise CoverageCalculationError(
                "intersection_area_m2, field_area_m2'den büyük olamaz."
            )

        coverage_ratio = intersection_area_m2 / field_area_m2
        is_sufficient = coverage_ratio >= self._min_coverage

        return CoverageResult(
            mission_id=mission_id,
            field_id=field_id,
            field_area_m2=field_area_m2,
            footprint_area_m2=footprint_area_m2,
            intersection_area_m2=intersection_area_m2,
            coverage_ratio=coverage_ratio,
            is_sufficient=is_sufficient,
            minimum_coverage_ratio=self._min_coverage,
        )

    @staticmethod
    def shoelace_area(polygon: Polygon) -> float:
        """Shoelace formülü ile polygon alanını hesaplar (yaklaşık, düzlemsel).

        Küçük alanlar için (tarla ölçeğinde) yeterli hassasiyettedir.
        Büyük alanlarda projeksiyon dönüşümü gerekir.

        Args:
            polygon: Koordinat listesi.

        Returns:
            Alan (birim²). Koordinatlar derece ise sonuç yaklaşıktır.
        """
        coords = polygon.coordinates
        n = len(coords) - 1  # Son nokta = ilk nokta (kapalı polygon)
        area = 0.0
        for i in range(n):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0

    @staticmethod
    def point_in_polygon(
        point: tuple[float, float],
        polygon: Polygon,
    ) -> bool:
        """Ray casting algoritması ile noktanın polygon içinde olup olmadığını kontrol eder.

        Args:
            point: (x, y) koordinatı.
            polygon: Test edilecek polygon.

        Returns:
            Nokta polygon içinde mi.
        """
        x, y = point
        coords = polygon.coordinates
        n = len(coords) - 1
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = coords[i]
            xj, yj = coords[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside
