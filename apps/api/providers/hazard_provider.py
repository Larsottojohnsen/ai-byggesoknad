"""
HazardProvider – adapter for NVE flom- og skreddata
NVE ArcGIS REST API: https://nve.geodataonline.no/arcgis/rest/services/
Available services (confirmed): FlomAktsomhet, Flomsoner1, Flomsoner2, Skredfaresoner1, Fjellskred1
"""
import httpx
import structlog
from typing import Optional
from core.cache import cache_get, cache_set
from models.schemas import HazardResult, HazardLevel

logger = structlog.get_logger()

# NVE ArcGIS REST services
# kart.nve.no is the public-facing endpoint (confirmed working)
# nve.geodataonline.no is blocked from some networks
NVE_BASE_PRIMARY = "https://kart.nve.no/enterprise/rest/services"
NVE_BASE_FALLBACK = "https://nve.geodataonline.no/arcgis/rest/services"
NVE_FLOM_URL = f"{NVE_BASE_PRIMARY}/Flomaktsomhet/MapServer/identify"
NVE_FLOM_URL_FALLBACK = f"{NVE_BASE_FALLBACK}/FlomAktsomhet/MapServer/identify"
NVE_SKRED_URL = f"{NVE_BASE_PRIMARY}/Skredfaresoner/MapServer/identify"
NVE_SKRED_URL_FALLBACK = f"{NVE_BASE_FALLBACK}/Skredfaresoner1/MapServer/identify"

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

        data_available = flom_fare != HazardLevel.ukjent or skred_fare != HazardLevel.ukjent
        result = HazardResult(
            flomFare=flom_fare,
            skredFare=skred_fare,
            notes="Data fra NVE Atlas" if data_available else "NVE data utilgjengelig",
        )

        await cache_set(cache_key, result.model_dump(), CACHE_TTL)
        return result

    def _build_identify_params(self, lat: float, lng: float) -> dict:
        """Build common ArcGIS identify parameters."""
        delta = 0.01  # ~1km search radius
        return {
            "f": "json",
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "sr": "4326",
            "layers": "all",
            "tolerance": 5,
            "mapExtent": f"{lng-delta},{lat-delta},{lng+delta},{lat+delta}",
            "imageDisplay": "100,100,96",
        }

    async def _check_flood_risk(self, lat: float, lng: float) -> HazardLevel:
        """Check flood risk using NVE FlomAktsomhet (kart.nve.no with fallback)."""
        for url in [NVE_FLOM_URL, NVE_FLOM_URL_FALLBACK]:
            try:
                response = await self.client.get(
                    url,
                    params=self._build_identify_params(lat, lng),
                    timeout=12.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        for r in results:
                            attrs = r.get("attributes", {})
                            # NVE FlomAktsomhet uses FLOMSONE or AKTSOMHET field
                            zone = (
                                attrs.get("FLOMSONE") or
                                attrs.get("AKTSOMHET") or
                                attrs.get("flomsone") or
                                attrs.get("aktsomhet") or
                                attrs.get("VassOmr") or
                                ""
                            )
                            level = self._map_nve_zone(str(zone))
                            if level != HazardLevel.ukjent:
                                logger.info("flood_risk_found", lat=lat, lng=lng, zone=zone, level=level.value, url=url)
                                return level
                        # Results found but no recognized zone - means area is in flood zone
                        logger.info("flood_risk_zone_found", lat=lat, lng=lng, count=len(results))
                        return HazardLevel.middels
                    else:
                        # No results = no flood risk in this area
                        logger.info("flood_risk_none", lat=lat, lng=lng, url=url)
                        return HazardLevel.ingen
                else:
                    logger.warning("flood_check_http_error", status=response.status_code, url=url)

            except Exception as e:
                logger.warning("flood_check_error", lat=lat, lng=lng, error=str(e), url=url)

        return HazardLevel.ukjent

    async def _check_landslide_risk(self, lat: float, lng: float) -> HazardLevel:
        """Check landslide risk using NVE Skredfaresoner (kart.nve.no with fallback)."""
        for url in [NVE_SKRED_URL, NVE_SKRED_URL_FALLBACK]:
            try:
                response = await self.client.get(
                    url,
                    params=self._build_identify_params(lat, lng),
                    timeout=12.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        for r in results:
                            attrs = r.get("attributes", {})
                            zone = (
                                attrs.get("SKREDSONE") or
                                attrs.get("AKTSOMHET") or
                                attrs.get("skredsone") or
                                attrs.get("aktsomhet") or
                                ""
                            )
                            level = self._map_nve_zone(str(zone))
                            if level != HazardLevel.ukjent:
                                logger.info("landslide_risk_found", lat=lat, lng=lng, zone=zone, level=level.value, url=url)
                                return level
                        # Results found but no recognized zone
                        return HazardLevel.middels
                    else:
                        # No results = no landslide risk
                        logger.info("landslide_risk_none", lat=lat, lng=lng, url=url)
                        return HazardLevel.ingen
                else:
                    logger.warning("landslide_check_http_error", status=response.status_code, url=url)

            except Exception as e:
                logger.warning("landslide_check_error", lat=lat, lng=lng, error=str(e), url=url)

        return HazardLevel.ukjent

    def _map_nve_zone(self, zone_str: str) -> HazardLevel:
        """Map NVE zone classification to our HazardLevel enum."""
        zone_lower = zone_str.lower().strip()
        if not zone_str or zone_str in ("None", "null", ""):
            return HazardLevel.ukjent
        if any(x in zone_lower for x in ["høy", "hoy", "3", "rød", "rod", "high"]):
            return HazardLevel.høy
        elif any(x in zone_lower for x in ["middels", "2", "gul", "orange", "medium"]):
            return HazardLevel.middels
        elif any(x in zone_lower for x in ["lav", "1", "grønn", "gronn", "low"]):
            return HazardLevel.lav
        elif any(x in zone_lower for x in ["ingen", "0", "none", "no"]):
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
