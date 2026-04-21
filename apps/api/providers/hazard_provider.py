"""
HazardProvider – adapter for NVE flom- og skreddata
NVE Atlas API: https://gis3.nve.no/arcgis/rest/services/
"""
import httpx
import structlog
from typing import Optional
from core.cache import cache_get, cache_set
from models.schemas import HazardResult, HazardLevel

logger = structlog.get_logger()

# NVE ArcGIS REST services
NVE_FLOM_URL = "https://gis3.nve.no/arcgis/rest/services/wmts/KartTjenester/MapServer/identify"
NVE_SKRED_URL = "https://gis3.nve.no/arcgis/rest/services/wmts/KartTjenester/MapServer/identify"

# NVE WMS for simpler queries
NVE_WMS_FLOM = "https://gis3.nve.no/arcgis/rest/services/Flom/FlomAktsomhet/MapServer"
NVE_WMS_SKRED = "https://gis3.nve.no/arcgis/rest/services/Skred/SkredAktsomhet/MapServer"

CACHE_TTL = 86400  # 24 hours


class HazardProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def lookup(self, lat: float, lng: float) -> HazardResult:
        """Look up hazard data for given coordinates."""
        cache_key = f"hazard:{lat:.4f}:{lng:.4f}"
        cached = await cache_get(cache_key)
        if cached:
            return HazardResult(**cached)

        flom_fare = await self._check_flood_risk(lat, lng)
        skred_fare = await self._check_landslide_risk(lat, lng)

        result = HazardResult(
            flomFare=flom_fare,
            skredFare=skred_fare,
            notes="Data fra NVE Atlas" if flom_fare != HazardLevel.ukjent else "NVE data utilgjengelig",
        )

        await cache_set(cache_key, result.model_dump(), CACHE_TTL)
        return result

    async def _check_flood_risk(self, lat: float, lng: float) -> HazardLevel:
        """Check flood risk using NVE flomaktsomhet."""
        try:
            # NVE ArcGIS identify query
            response = await self.client.get(
                f"{NVE_WMS_FLOM}/identify",
                params={
                    "f": "json",
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "sr": "4326",
                    "layers": "all",
                    "tolerance": 2,
                    "mapExtent": f"{lng-0.01},{lat-0.01},{lng+0.01},{lat+0.01}",
                    "imageDisplay": "100,100,96",
                },
                timeout=8.0,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    # Parse NVE flood zone classification
                    for r in results:
                        attrs = r.get("attributes", {})
                        zone = attrs.get("FLOMSONE", attrs.get("AKTSOMHET", ""))
                        return self._map_nve_zone(str(zone))

        except Exception as e:
            logger.warning("flood_check_error", lat=lat, lng=lng, error=str(e))

        return HazardLevel.ukjent

    async def _check_landslide_risk(self, lat: float, lng: float) -> HazardLevel:
        """Check landslide risk using NVE skredaktsomhet."""
        try:
            response = await self.client.get(
                f"{NVE_WMS_SKRED}/identify",
                params={
                    "f": "json",
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "sr": "4326",
                    "layers": "all",
                    "tolerance": 2,
                    "mapExtent": f"{lng-0.01},{lat-0.01},{lng+0.01},{lat+0.01}",
                    "imageDisplay": "100,100,96",
                },
                timeout=8.0,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    for r in results:
                        attrs = r.get("attributes", {})
                        zone = attrs.get("SKREDSONE", attrs.get("AKTSOMHET", ""))
                        return self._map_nve_zone(str(zone))

        except Exception as e:
            logger.warning("landslide_check_error", lat=lat, lng=lng, error=str(e))

        return HazardLevel.ukjent

    def _map_nve_zone(self, zone_str: str) -> HazardLevel:
        """Map NVE zone classification to our HazardLevel enum."""
        zone_lower = zone_str.lower()
        if any(x in zone_lower for x in ["høy", "hoy", "3", "rød", "rod"]):
            return HazardLevel.høy
        elif any(x in zone_lower for x in ["middels", "2", "gul", "orange"]):
            return HazardLevel.middels
        elif any(x in zone_lower for x in ["lav", "1", "grønn", "gronn"]):
            return HazardLevel.lav
        elif any(x in zone_lower for x in ["ingen", "0"]):
            return HazardLevel.ingen
        return HazardLevel.ukjent

    async def close(self):
        await self.client.aclose()


_hazard_provider: Optional[HazardProvider] = None


def get_hazard_provider() -> HazardProvider:
    global _hazard_provider
    if _hazard_provider is None:
        _hazard_provider = HazardProvider()
    return _hazard_provider
