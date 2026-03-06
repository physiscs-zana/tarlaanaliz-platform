# PATH: src/infrastructure/external/tkgm_megsis_wfs_adapter.py
# DESC: TKGM/MEGSİS WFS/WMS proxy üzerinden parsel geometrisi sorgulayan adapter (ParcelGeometryProvider impl).
"""
TKGM/MEGSİS WFS adapter: kadastro parsel geometrisi sorgulama.

WFS/WMS proxy üzerinden TKGM/MEGSİS'ten parsel geometrisi ve alan
bilgisi sorgular. Cache destekli; parsel geometrisi nadiren değişir.

Graceful degradation: TKGM erişilemezse None döner.
Retry: Transient hatalarda exponential backoff.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Optional

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.domain.value_objects.parcel_ref import ParcelRef
from src.core.ports.external.parcel_geometry_provider import (
    ParcelGeometry,
    ParcelGeometryProvider,
    ParcelValidationResult,
)
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    reraise=True,
)


class TKGMMegsisWFSAdapter(ParcelGeometryProvider):
    """ParcelGeometryProvider port implementasyonu (TKGM/MEGSİS WFS).

    httpx async HTTP client ile TKGM WFS proxy'ye bağlanır.
    Bellek içi cache ile sık sorgulanan parseller cache'lenir.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.tkgm_wfs_base_url
        self._timeout = httpx.Timeout(settings.tkgm_wfs_timeout_seconds)
        self._cache_ttl = settings.tkgm_cache_ttl_seconds
        self._cache: dict[str, tuple[float, ParcelGeometry]] = {}

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={"Accept": "application/json"},
        )

    def _cache_key(self, parcel_ref: ParcelRef) -> str:
        return parcel_ref.unique_hash

    def _get_cached(self, parcel_ref: ParcelRef) -> Optional[ParcelGeometry]:
        """Cache'ten parsel geometrisi döner (TTL kontrolü ile)."""
        key = self._cache_key(parcel_ref)
        entry = self._cache.get(key)
        if entry is None:
            return None
        cached_at, geometry = entry
        now = asyncio.get_event_loop().time()
        if now - cached_at > self._cache_ttl:
            del self._cache[key]
            return None
        return geometry

    def _set_cached(self, parcel_ref: ParcelRef, geometry: ParcelGeometry) -> None:
        """Parsel geometrisini cache'e yazar."""
        key = self._cache_key(parcel_ref)
        now = asyncio.get_event_loop().time()
        self._cache[key] = (now, geometry)

    @_RETRY_DECORATOR
    async def get_geometry(
        self,
        parcel_ref: ParcelRef,
    ) -> Optional[ParcelGeometry]:
        """Parsel geometrisini TKGM/MEGSİS'ten sorgula (cache destekli)."""
        cached = self._get_cached(parcel_ref)
        if cached is not None:
            logger.debug("tkgm_cache_hit", parcel_ref=str(parcel_ref))
            return cached

        logger.info("tkgm_geometry_request", parcel_ref=str(parcel_ref))

        async with self._get_client() as client:
            response = await client.get(
                "/wfs",
                params={
                    "service": "WFS",
                    "request": "GetFeature",
                    "typeName": "kadastro:parsel",
                    "outputFormat": "application/json",
                    "CQL_FILTER": (
                        f"il='{parcel_ref.province}' AND "
                        f"ilce='{parcel_ref.district}' AND "
                        f"mahalle='{parcel_ref.village}' AND "
                        f"ada='{parcel_ref.ada}' AND "
                        f"parsel='{parcel_ref.parsel}'"
                    ),
                },
            )
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        if not features:
            logger.info("tkgm_parcel_not_found", parcel_ref=str(parcel_ref))
            return None

        feature = features[0]
        geometry_data = feature.get("geometry", {})
        properties = feature.get("properties", {})
        area_m2 = Decimal(str(properties.get("alan", 0)))

        result = ParcelGeometry(
            parcel_ref=parcel_ref,
            geometry=geometry_data,
            area_m2=area_m2,
            coordinate_system=data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326"),
        )

        self._set_cached(parcel_ref, result)
        logger.info("tkgm_geometry_success", parcel_ref=str(parcel_ref), area_m2=str(area_m2))
        return result

    @_RETRY_DECORATOR
    async def validate_parcel(
        self,
        parcel_ref: ParcelRef,
        declared_area_m2: Optional[Decimal] = None,
    ) -> ParcelValidationResult:
        """Parsel varlığını ve alan tutarlılığını doğrula (KR-013)."""
        geometry = await self.get_geometry(parcel_ref)

        if geometry is None:
            return ParcelValidationResult(
                exists=False,
                parcel_ref=parcel_ref,
                message="Parsel TKGM kaydında bulunamadı.",
            )

        area_deviation: Optional[Decimal] = None
        if declared_area_m2 is not None and geometry.area_m2 > 0:
            area_deviation = abs(declared_area_m2 - geometry.area_m2) / geometry.area_m2 * Decimal("100")

        return ParcelValidationResult(
            exists=True,
            parcel_ref=parcel_ref,
            area_m2=geometry.area_m2,
            area_deviation_pct=area_deviation,
            message="Parsel doğrulandı.",
        )

    async def get_geometries_batch(
        self,
        parcel_refs: list[ParcelRef],
    ) -> list[ParcelGeometry]:
        """Birden fazla parselin geometrisini toplu sorgula."""
        results: list[ParcelGeometry] = []
        for ref in parcel_refs:
            geometry = await self.get_geometry(ref)
            if geometry is not None:
                results.append(geometry)
        return results

    async def health_check(self) -> bool:
        """TKGM/MEGSİS servisinin erişilebilirliğini kontrol et."""
        try:
            async with self._get_client() as client:
                response = await client.get(
                    "/wfs",
                    params={
                        "service": "WFS",
                        "request": "GetCapabilities",
                    },
                )
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            logger.warning("tkgm_health_check_failed")
            return False
