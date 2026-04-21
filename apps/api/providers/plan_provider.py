"""
PlanProvider – adapter for Geonorge OGC API Features (reguleringsplaner)
Uses Geonorge's national plan registry.
"""
import httpx
import structlog
from typing import Optional, List, Dict, Any
from core.cache import cache_get, cache_set
from models.schemas import PlanLayerResult, PlanStatus

logger = structlog.get_logger()

# Geonorge OGC API for reguleringsplaner
PLAN_API_BASE = "https://ogcapitest.kartverket.no/rest/services/reguleringsplanforslag/v1"
# Fallback WMS for kommuneplan
KOMMUNEPLAN_WMS = "https://wms.geonorge.no/skwms1/wms.arealressurskart2"
CACHE_TTL = 21600  # 6 hours


class PlanProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def lookup(self, lat: float, lng: float) -> Optional[PlanLayerResult]:
        """Look up plan layers for given coordinates."""
        cache_key = f"plan:{lat:.4f}:{lng:.4f}"
        cached = await cache_get(cache_key)
        if cached:
            return PlanLayerResult(**cached)

        result = await self._try_ogc_api(lat, lng)
        if not result:
            result = await self._try_wfs_fallback(lat, lng)
        if not result:
            result = self._create_unknown_plan()

        await cache_set(cache_key, result.model_dump(), CACHE_TTL)
        return result

    async def _try_ogc_api(self, lat: float, lng: float) -> Optional[PlanLayerResult]:
        """Try Geonorge OGC API Features."""
        try:
            # Use a bounding box around the point
            delta = 0.001  # ~100m
            bbox = f"{lng-delta},{lat-delta},{lng+delta},{lat+delta}"

            response = await self.client.get(
                f"{PLAN_API_BASE}/collections/reguleringsplanforslag/items",
                params={
                    "bbox": bbox,
                    "bbox-crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                    "f": "json",
                    "limit": 5,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    return self._parse_plan_feature(features[0])

        except Exception as e:
            logger.warning("plan_ogc_api_error", lat=lat, lng=lng, error=str(e))

        return None

    async def _try_wfs_fallback(self, lat: float, lng: float) -> Optional[PlanLayerResult]:
        """Fallback: try Kartverket WFS for plan data."""
        try:
            response = await self.client.get(
                "https://wfs.geonorge.no/skwms1/wfs.reguleringsplaner",
                params={
                    "SERVICE": "WFS",
                    "VERSION": "2.0.0",
                    "REQUEST": "GetFeature",
                    "TYPENAMES": "app:Reguleringsplan",
                    "CQL_FILTER": f"INTERSECTS(omrade, POINT({lng} {lat}))",
                    "SRSNAME": "EPSG:4326",
                    "outputFormat": "application/json",
                    "count": 3,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    return self._parse_plan_feature(features[0])

        except Exception as e:
            logger.warning("plan_wfs_fallback_error", lat=lat, lng=lng, error=str(e))

        return None

    def _parse_plan_feature(self, feature: Dict[str, Any]) -> PlanLayerResult:
        props = feature.get("properties", {})
        geom = feature.get("geometry")

        # Map Norwegian plan types to our enum
        plan_type = props.get("plantype", "").lower()
        if "reguleringsplan" in plan_type or "detaljregulering" in plan_type:
            status = PlanStatus.regulert
        elif "kommuneplan" in plan_type or "kommunedelplan" in plan_type:
            status = PlanStatus.kommuneplan
        else:
            status = PlanStatus.ukjent

        # Try to extract arealformål
        areal_formal = props.get("arealformål", props.get("formål", "ukjent"))
        if isinstance(areal_formal, str):
            areal_formal = areal_formal.lower()

        hensynssoner = []
        if props.get("hensynssone"):
            hensynssoner = [props["hensynssone"]] if isinstance(props["hensynssone"], str) else props["hensynssone"]

        return PlanLayerResult(
            planId=props.get("planidentifikasjon") or props.get("planid"),
            planName=props.get("plannavn") or props.get("planname"),
            planStatus=status,
            arealFormål=areal_formal or "ukjent",
            hensynssoner=hensynssoner,
            byggegrense=props.get("byggegrense"),
            utnyttelsesgrad=props.get("utnyttelsesgrad") or props.get("bya"),
            planUrl=props.get("planUrl"),
            geometry={"type": "Feature", "geometry": geom, "properties": {}} if geom else None,
        )

    def _create_unknown_plan(self) -> PlanLayerResult:
        return PlanLayerResult(
            planStatus=PlanStatus.ukjent,
            arealFormål="ukjent",
            hensynssoner=[],
        )

    async def close(self):
        await self.client.aclose()


_plan_provider: Optional[PlanProvider] = None


def get_plan_provider() -> PlanProvider:
    global _plan_provider
    if _plan_provider is None:
        _plan_provider = PlanProvider()
    return _plan_provider
