"""
PlanProvider – adapter for Norwegian arealplan/reguleringsplan data
Uses Geonorge WFS service for reguleringsplan lookup by coordinates.
Falls back to kommuneplan if no reguleringsplan found.
"""
import httpx
import structlog
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
from core.cache import cache_get, cache_set
from models.schemas import PlanLayerResult, PlanStatus

logger = structlog.get_logger()

# Geonorge WFS for reguleringsplaner (open, no auth required)
GEONORGE_WFS_BASE = "https://wfs.geonorge.no/skwms1/wfs.reguleringsplaner"
CACHE_TTL = 21600  # 6 hours


class PlanProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0)

    async def lookup(self, lat: float, lng: float, kommunenr: str = None) -> Optional[PlanLayerResult]:
        """Look up plan layers for given coordinates."""
        cache_key = f"plan:{lat:.4f}:{lng:.4f}"
        cached = await cache_get(cache_key)
        if cached:
            return PlanLayerResult(**cached)

        result = None

        # Try Geonorge WFS for reguleringsplan
        result = await self._try_geonorge_wfs(lat, lng)

        if not result:
            result = self._create_unknown_plan()

        await cache_set(cache_key, result.model_dump(), CACHE_TTL)
        return result

    async def _try_geonorge_wfs(self, lat: float, lng: float) -> Optional[PlanLayerResult]:
        """Try Geonorge WFS for reguleringsplan data."""
        # Small bounding box around the point (~200m)
        delta = 0.002
        bbox = f"{lng - delta},{lat - delta},{lng + delta},{lat + delta},EPSG:4326"

        try:
            response = await self.client.get(
                GEONORGE_WFS_BASE,
                params={
                    "SERVICE": "WFS",
                    "VERSION": "2.0.0",
                    "REQUEST": "GetFeature",
                    "TYPENAMES": "app:Reguleringsplanomrade",
                    "COUNT": "5",
                    "BBOX": bbox,
                    "OUTPUTFORMAT": "application/json",
                },
                timeout=15.0,
            )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = response.json()
                    features = data.get("features", [])
                    if features:
                        best = self._pick_best_feature(features)
                        if best:
                            result = self._parse_geojson_feature(best)
                            logger.info("plan_found_wfs", lat=lat, lng=lng, plan_id=result.planId)
                            return result
                    else:
                        logger.info("plan_no_results_wfs", lat=lat, lng=lng)
                elif "xml" in content_type or "gml" in content_type:
                    # Try to parse GML/XML response
                    result = self._parse_gml_response(response.text, lat, lng)
                    if result:
                        return result
            else:
                logger.warning("plan_wfs_http_error", status=response.status_code, lat=lat, lng=lng)

        except Exception as e:
            logger.warning("plan_wfs_error", lat=lat, lng=lng, error=str(e))

        return None

    def _pick_best_feature(self, features: list) -> Optional[Dict]:
        """Pick the most specific plan from a list of GeoJSON features."""
        if not features:
            return None

        # Prefer detaljregulering over reguleringsplan over kommuneplan
        priority_order = ["detaljregulering", "reguleringsplan", "regulering", "kommuneplan"]
        for priority in priority_order:
            for f in features:
                props = f.get("properties", {})
                plantype = str(props.get("plantype", props.get("planType", ""))).lower()
                if priority in plantype:
                    return f

        return features[0]

    def _parse_geojson_feature(self, feature: Dict[str, Any]) -> PlanLayerResult:
        """Parse a GeoJSON feature into PlanLayerResult."""
        props = feature.get("properties", {})

        plantype = str(props.get("plantype", props.get("planType", ""))).lower()
        if "detaljregulering" in plantype or "reguleringsplan" in plantype or "regulering" in plantype:
            status = PlanStatus.regulert
        elif "kommuneplan" in plantype or "kommunedelplan" in plantype:
            status = PlanStatus.kommuneplan
        else:
            status = PlanStatus.regulert  # Default for WFS results

        plan_id = (
            props.get("planidentifikasjon") or
            props.get("planId") or
            props.get("planid") or
            props.get("lokal_id") or
            props.get("id")
        )
        plan_name = (
            props.get("plannavn") or
            props.get("planNavn") or
            props.get("name") or
            props.get("planname") or
            plantype.title()
        )

        areal_formal = (
            props.get("arealformål") or
            props.get("arealFormål") or
            props.get("formål") or
            props.get("planformål") or
            "boligbebyggelse"  # Most common for residential areas
        )
        if isinstance(areal_formal, str):
            areal_formal = areal_formal.lower()

        return PlanLayerResult(
            planId=str(plan_id) if plan_id else None,
            planName=plan_name,
            planStatus=status,
            arealFormål=areal_formal or "ukjent",
            hensynssoner=[],
            byggegrense=None,
            utnyttelsesgrad=None,
            planUrl=props.get("planUrl") or props.get("planurl"),
            geometry=None,
        )

    def _parse_gml_response(self, xml_text: str, lat: float, lng: float) -> Optional[PlanLayerResult]:
        """Parse GML/XML WFS response."""
        try:
            root = ET.fromstring(xml_text)
            ns = {
                "wfs": "http://www.opengis.net/wfs/2.0",
                "app": "http://skjema.geonorge.no/SOSI/produktspesifikasjon/Reguleringsplanforslag/20170401",
            }
            members = root.findall(".//wfs:member", ns) or root.findall(".//{*}member")
            if members:
                logger.info("plan_found_gml", lat=lat, lng=lng, count=len(members))
                return PlanLayerResult(
                    planId=None,
                    planName="Reguleringsplan (GML)",
                    planStatus=PlanStatus.regulert,
                    arealFormål="ukjent",
                    hensynssoner=[],
                )
        except Exception as e:
            logger.warning("plan_gml_parse_error", error=str(e))
        return None

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
