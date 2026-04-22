"""
PropertyProvider – adapter for Kartverket Matrikkel REST API
Uses ws.geonorge.no/eiendom/v1/punkt for property lookup by coordinates.
"""
import httpx
import structlog
from typing import Optional, Dict, Any
from core.cache import cache_get, cache_set
from models.schemas import PropertyData

logger = structlog.get_logger()

# Kartverket Matrikkel REST API (confirmed working)
MATRIKKEL_REST_URL = "https://ws.geonorge.no/eiendom/v1/punkt"
CACHE_TTL = 86400  # 24 hours


class PropertyProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def lookup_by_coordinates(self, lat: float, lng: float) -> Optional[PropertyData]:
        """Look up property at given coordinates using Kartverket Matrikkel REST API."""
        cache_key = f"property:coord:{lat:.5f}:{lng:.5f}"
        cached = await cache_get(cache_key)
        if cached:
            return PropertyData(**cached)

        try:
            response = await self.client.get(
                MATRIKKEL_REST_URL,
                params={
                    "nord": lat,
                    "ost": lng,
                    "koordsys": 4326,
                },
                timeout=12.0,
            )

            if response.status_code == 200:
                data = response.json()
                eiendommer = data.get("eiendom", [])
                if eiendommer:
                    # Pick the first (closest) property
                    eiendom = eiendommer[0]
                    result = self._parse_eiendom(eiendom, lat, lng)
                    await cache_set(cache_key, result.model_dump(), CACHE_TTL)
                    return result

            logger.warning("matrikkel_rest_no_data", status=response.status_code, lat=lat, lng=lng)

        except Exception as e:
            logger.warning("property_lookup_error", lat=lat, lng=lng, error=str(e))

        # Fallback: return minimal property from coordinate
        return self._create_minimal_property(lat, lng)

    def _parse_eiendom(self, eiendom: Dict[str, Any], lat: float, lng: float) -> PropertyData:
        """Parse a Matrikkel REST eiendom object into PropertyData."""
        kommunenr = str(eiendom.get("kommunenummer", "0000"))
        gnr = int(eiendom.get("gardsnummer", 0))
        bnr = int(eiendom.get("bruksnummer", 0))
        fnr = eiendom.get("festenummer")
        snr = eiendom.get("seksjonsnummer")
        matrikkelnr = eiendom.get("matrikkelnummertekst", f"{gnr}/{bnr}")

        # Get representative point
        rep_punkt = eiendom.get("representasjonspunkt", {})
        geom = None
        if rep_punkt:
            geom = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [rep_punkt.get("øst", lng), rep_punkt.get("nord", lat)]
                },
                "properties": {}
            }

        return PropertyData(
            id=f"{kommunenr}-{matrikkelnr}",
            municipalityNumber=kommunenr,
            municipality=None,  # Will be enriched from municipality_provider
            gnr=gnr,
            bnr=bnr,
            fnr=fnr if fnr and fnr != 0 else None,
            snr=snr if snr and snr != 0 else None,
            areal=None,  # Not available from this endpoint
            buildingStatus=None,
            geometry=geom,
            address=None,
        )

    def _create_minimal_property(self, lat: float, lng: float) -> PropertyData:
        """Fallback: create minimal property data when API fails."""
        return PropertyData(
            id=f"coord-{lat:.5f}-{lng:.5f}",
            municipalityNumber="0000",
            municipality="Ukjent (Matrikkel utilgjengelig)",
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
