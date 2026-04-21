"""
PropertyProvider – adapter for Kartverket Matrikkel / WFS eiendomsdata
Uses Kartverket's WFS service for property boundaries and metadata.
"""
import httpx
import structlog
from typing import Optional, Dict, Any
from core.config import settings
from core.cache import cache_get, cache_set
from models.schemas import PropertyData

logger = structlog.get_logger()

# Kartverket WFS for eiendomsgrenser
PROPERTY_WFS_URL = "https://wfs.geonorge.no/skwms1/wfs.eiendomskart"
CACHE_TTL = 86400  # 24 hours


class PropertyProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def lookup_by_coordinates(self, lat: float, lng: float) -> Optional[PropertyData]:
        """Look up property at given coordinates using WFS point-in-polygon."""
        cache_key = f"property:coord:{lat:.5f}:{lng:.5f}"
        cached = await cache_get(cache_key)
        if cached:
            return PropertyData(**cached)

        try:
            # Use Kartverket WFS GetFeature with CQL filter
            # Convert lat/lng to UTM33N for Norwegian WFS services
            response = await self.client.get(
                PROPERTY_WFS_URL,
                params={
                    "SERVICE": "WFS",
                    "VERSION": "2.0.0",
                    "REQUEST": "GetFeature",
                    "TYPENAMES": "app:MatrikkelBubble",
                    "CQL_FILTER": f"INTERSECTS(geometry, POINT({lng} {lat}))",
                    "SRSNAME": "EPSG:4326",
                    "outputFormat": "application/json",
                    "count": 1,
                },
            )

            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    return self._parse_feature(features[0], lat, lng)

            # Fallback: return minimal property from coordinate
            return self._create_minimal_property(lat, lng)

        except Exception as e:
            logger.warning("property_lookup_error", lat=lat, lng=lng, error=str(e))
            return self._create_minimal_property(lat, lng)

    def _parse_feature(self, feature: Dict[str, Any], lat: float, lng: float) -> PropertyData:
        props = feature.get("properties", {})
        geom = feature.get("geometry")

        return PropertyData(
            id=str(props.get("matrikkelnummer", f"{lat:.4f}-{lng:.4f}")),
            municipalityNumber=str(props.get("kommunenummer", "0000")),
            municipality=props.get("kommunenavn", "Ukjent"),
            gnr=int(props.get("gardsnummer", 0)),
            bnr=int(props.get("bruksnummer", 0)),
            fnr=props.get("festenummer"),
            snr=props.get("seksjonsnummer"),
            areal=props.get("areal_beregnet"),
            buildingStatus=props.get("bygningsstatus"),
            geometry={"type": "Feature", "geometry": geom, "properties": {}} if geom else None,
        )

    def _create_minimal_property(self, lat: float, lng: float) -> PropertyData:
        """Fallback: create minimal property data when WFS fails."""
        return PropertyData(
            id=f"coord-{lat:.5f}-{lng:.5f}",
            municipalityNumber="0000",
            municipality="Ukjent (WFS utilgjengelig)",
            gnr=0,
            bnr=0,
            areal=None,
        )

    async def close(self):
        await self.client.aclose()


_property_provider: Optional[PropertyProvider] = None


def get_property_provider() -> PropertyProvider:
    global _property_provider
    if _property_provider is None:
        _property_provider = PropertyProvider()
    return _property_provider
