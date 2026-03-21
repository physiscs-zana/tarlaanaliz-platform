# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/geometry.py
# DESC: Geometry VO; polygon/point verileri Shapely ile sarmalama.

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from shapely.geometry import MultiPolygon, Point, Polygon
    from shapely.geometry import mapping as shapely_mapping
    from shapely.geometry import shape as shapely_shape

try:
    from shapely.geometry import MultiPolygon, Point, Polygon  # noqa: F811
    from shapely.geometry import mapping as shapely_mapping  # noqa: F811
    from shapely.geometry import shape as shapely_shape  # noqa: F811

    _HAS_SHAPELY = True
except ImportError:
    _HAS_SHAPELY = False


class GeometryError(Exception):
    """Geometry domain invariant ihlali."""


@dataclass(frozen=True)
class Geometry:
    """Coğrafi geometri değer nesnesi (KR-016, KR-081).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    Shapely geometri nesnesini sarmalar ve GeoJSON (RFC 7946) ile
    serileştirme/deserileştirme sağlar.

    Kullanım alanları:
    - Tarla sınırları (field boundary) (KR-016)
    - Mission kapsama alanları (coverage areas)
    - Training feedback GeoJSON export
    - Uçuş rotası geometrileri

    Invariants:
    - _shape geçerli bir Shapely geometri nesnesi olmalıdır.
    - Geometri geçerli (valid) olmalıdır.
    - Geometri boş (empty) olmamalıdır.
    """

    _shape: Polygon | MultiPolygon | Point

    def __post_init__(self) -> None:
        if self._shape is None:
            raise GeometryError("Geometri nesnesi None olamaz.")
        if not hasattr(self._shape, "is_valid"):
            raise GeometryError(
                f"Geçersiz geometri tipi: {type(self._shape).__name__}. "
                "Shapely Polygon, MultiPolygon veya Point bekleniyor."
            )
        if self._shape.is_empty:
            raise GeometryError("Geometri boş olamaz.")
        if not self._shape.is_valid:
            raise GeometryError(f"Geçersiz geometri: {self._shape.geom_type}")

    @classmethod
    def from_geojson(cls, geojson: dict[str, Any]) -> Geometry:
        """GeoJSON dict'ten Geometry oluşturur (RFC 7946).

        Args:
            geojson: {"type": "Polygon", "coordinates": [...]} formatında dict.

        Raises:
            GeometryError: Geçersiz GeoJSON veya geometri.
        """
        if not isinstance(geojson, dict):
            raise GeometryError(f"GeoJSON dict olmalıdır, alınan tip: {type(geojson).__name__}")
        if "type" not in geojson or "coordinates" not in geojson:
            raise GeometryError("GeoJSON 'type' ve 'coordinates' alanlarını içermelidir.")
        try:
            shape = shapely_shape(geojson)
        except Exception as exc:
            raise GeometryError(f"GeoJSON parse hatası: {exc}") from exc
        return cls(_shape=shape)

    @classmethod
    def from_polygon_coords(cls, coordinates: list[list[list[float]]]) -> Geometry:
        """Polygon koordinatlarından Geometry oluşturur.

        Args:
            coordinates: GeoJSON Polygon coordinates formatı.
                [[lon, lat], [lon, lat], ...] (outer ring, optional inner rings)
        """
        return cls.from_geojson({"type": "Polygon", "coordinates": coordinates})

    @classmethod
    def from_point(cls, longitude: float, latitude: float) -> Geometry:
        """Nokta koordinatlarından Geometry oluşturur.

        Args:
            longitude: Boylam.
            latitude: Enlem.
        """
        return cls(_shape=Point(longitude, latitude))

    @property
    def geom_type(self) -> str:
        """Geometri tipi (Polygon, MultiPolygon, Point)."""
        return cast(str, self._shape.geom_type)

    @property
    def area(self) -> float:
        """Geometri alanı (derece kare; kesin hesap için projeksiyon gerekir)."""
        return float(self._shape.area)

    @property
    def centroid(self) -> tuple[float, float]:
        """Ağırlık merkezi (longitude, latitude)."""
        c = self._shape.centroid
        return (c.x, c.y)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Sınır kutusu (minx, miny, maxx, maxy)."""
        bounds = self._shape.bounds
        return (float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))

    def contains(self, other: Geometry) -> bool:
        """Bu geometri diğer geometriyi içeriyor mu?"""
        return bool(self._shape.contains(other._shape))

    def intersects(self, other: Geometry) -> bool:
        """Bu geometri diğer geometriyle kesişiyor mu?"""
        return bool(self._shape.intersects(other._shape))

    def intersection(self, other: Geometry) -> Geometry:
        """İki geometrinin kesişimini döner."""
        result = self._shape.intersection(other._shape)
        if result.is_empty:
            raise GeometryError("Kesişim sonucu boş geometri.")
        return Geometry(_shape=result)

    def coverage_ratio(self, other: Geometry) -> float:
        """Diğer geometrinin bu geometriyi kapsama oranı (0.0-1.0).

        KR-016 kapsama doğrulaması:
        - >= 0.95: TAM ödeme
        - >= 0.80: KISMİ + opsiyonel inceleme
        - < 0.80: TEKRAR UÇUŞ veya itiraz
        """
        if self._shape.area == 0:
            return 0.0
        intersection_area = float(self._shape.intersection(other._shape).area)
        return intersection_area / float(self._shape.area)

    def to_geojson(self) -> dict[str, Any]:
        """GeoJSON dict'e dönüştürür (RFC 7946)."""
        return cast(dict[str, Any], shapely_mapping(self._shape))

    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return self.to_geojson()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Geometry):
            return bool(self._shape.equals(other._shape))
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._shape.wkt)

    def __repr__(self) -> str:
        return f"Geometry(type='{self.geom_type}', bounds={self.bounds})"
