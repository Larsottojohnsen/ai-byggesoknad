"""
PlanProvider – fetches reguleringsplan data for a given coordinate.

Uses DiBK NAP WMS GetFeatureInfo (open, no auth required):
  https://nap.ft.dibk.no/services/wms/reguleringsplaner

Layer structure (vertikalnivå 2 = ground level):
  - rpomrade_vn2: Reguleringsplanområde (plan boundary)
  - arealformal_vn2: Arealformål (land use purpose)
  - hensynssoner_vn2: Hensynssoner (safety zones)

Falls back to kommuneplan/arealplaner.no link if WMS returns no data.

NOTE: Reguleringsplan data in Norway requires Norge Digitalt agreement for
vector downloads (OGC API Features). The WMS service is open but may return
empty results for areas not covered by a reguleringsplan.
"""
import math
import httpx
import structlog
from typing import Optional
from core.cache import cache_get, cache_set
from models.schemas import PlanLayer, PlanStatus

logger = structlog.get_logger()

WMS_BASE = "https://nap.ft.dibk.no/services/wms/reguleringsplaner"
CACHE_TTL = 3600  # 1 hour


def _build_bbox(lat: float, lng: float, delta: float = 0.005):
    """Build a small bounding box around a point (in CRS:84 = lon,lat order)."""
    return f"{lng - delta},{lat - delta},{lng + delta},{lat + delta}"


def _pixel_for_point(lat: float, lng: float, bbox_str: str, width: int = 101, height: int = 101):
    """Compute the pixel (I, J) for a lat/lng within a given BBOX."""
    parts = [float(x) for x in bbox_str.split(",")]
    min_lng, min_lat, max_lng, max_lat = parts
    i = int((lng - min_lng) / (max_lng - min_lng) * width)
    j = int((max_lat - lat) / (max_lat - min_lat) * height)
    # Clamp to image bounds
    i = max(0, min(width - 1, i))
    j = max(0, min(height - 1, j))
    return i, j


async def _wms_get_feature_info(
    lat: float, lng: float, layer: str, delta: float = 0.005
) -> Optional[dict]:
    """Call WMS GetFeatureInfo and return first feature properties, or None."""
    bbox = _build_bbox(lat, lng, delta)
    i, j = _pixel_for_point(lat, lng, bbox)

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer,
        "QUERY_LAYERS": layer,
        "INFO_FORMAT": "application/json",
        "I": i,
        "J": j,
        "WIDTH": 101,
        "HEIGHT": 101,
        "CRS": "CRS:84",
        "BBOX": bbox,
    }

    headers = {
        "User-Agent": "ai-byggesoknad/1.0 (byggesoknad.no; kontakt@byggesoknad.no)",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=12.0, headers=headers) as client:
            resp = await client.get(WMS_BASE, params=params)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    return features[0].get("properties", {})
    except Exception as e:
        logger.warning("wms_get_feature_info_error", layer=layer, error=str(e))

    return None


class PlanProvider:
    async def lookup(
        self, lat: float, lng: float, kommunenr: Optional[str] = None
    ) -> Optional[PlanLayer]:
        """Look up reguleringsplan for given coordinates using DiBK NAP WMS."""
        cache_key = f"plan:{lat:.4f}:{lng:.4f}"
        cached = await cache_get(cache_key)
        if cached:
            return PlanLayer(**cached)

        logger.info("plan_lookup_start", lat=lat, lng=lng, kommunenr=kommunenr)

        # Build arealplaner.no link for this municipality
        plan_register_url = None
        if kommunenr:
            plan_register_url = f"https://arealplaner.no/{kommunenr}/arealplaner"

        # Try WMS GetFeatureInfo for reguleringsplanområde (ground level, vn2)
        # Try multiple deltas to increase chance of hitting a plan
        props = None
        for delta in [0.003, 0.008, 0.015]:
            props = await _wms_get_feature_info(lat, lng, "rpomrade_vn2", delta=delta)
            if props:
                logger.info("plan_found_rpomrade", delta=delta, props=props)
                break

        if props:
            plan_id = props.get("planidentifikasjon") or props.get("planid") or props.get("lokal_id")
            plan_name = props.get("plannavn") or props.get("planNavn") or props.get("name")
            plan_status_raw = props.get("planstatus") or props.get("planStatus") or "gjeldende"
            areal_formal = props.get("arealformål") or props.get("arealFormål") or props.get("formål")

            # Map planstatus to our enum
            plan_status = _map_plan_status(plan_status_raw)

            result = PlanLayer(
                planId=str(plan_id) if plan_id else None,
                planName=plan_name,
                planStatus=plan_status,
                arealFormål=areal_formal or "ukjent",
                hensynssoner=[],
                byggegrense=None,
                utnyttelsesgrad=None,
                planUrl=plan_register_url,
            )
            await cache_set(cache_key, result.model_dump(), CACHE_TTL)
            return result

        # Try arealformal layer as fallback
        props_formal = await _wms_get_feature_info(lat, lng, "arealformal_vn2", delta=0.01)
        if props_formal:
            areal_formal = (
                props_formal.get("arealformål")
                or props_formal.get("arealFormål")
                or props_formal.get("formål")
                or props_formal.get("type")
            )
            result = PlanLayer(
                planId=None,
                planName="Reguleringsplan (arealformål funnet)",
                planStatus=PlanStatus.gjeldende,
                arealFormål=str(areal_formal) if areal_formal else "ukjent",
                hensynssoner=[],
                byggegrense=None,
                utnyttelsesgrad=None,
                planUrl=plan_register_url,
            )
            await cache_set(cache_key, result.model_dump(), CACHE_TTL)
            return result

        # No plan found – return unknown status with link to municipality plan register
        logger.info("plan_not_found", lat=lat, lng=lng, kommunenr=kommunenr)
        result = PlanLayer(
            planId=None,
            planName=None,
            planStatus=PlanStatus.ukjent,
            arealFormål="ukjent",
            hensynssoner=[],
            byggegrense=None,
            utnyttelsesgrad=None,
            planUrl=plan_register_url,
        )
        await cache_set(cache_key, result.model_dump(), CACHE_TTL)
        return result


def _map_plan_status(raw: str) -> PlanStatus:
    """Map raw planstatus string to our PlanStatus enum."""
    if not raw:
        return PlanStatus.ukjent
    raw_lower = raw.lower()
    if any(x in raw_lower for x in ["gjeldende", "vedtatt", "approved", "aktiv"]):
        return PlanStatus.gjeldende
    if any(x in raw_lower for x in ["forslag", "høring", "proposed", "draft"]):
        return PlanStatus.forslag
    if any(x in raw_lower for x in ["opphev", "utgått", "cancelled", "revoked"]):
        return PlanStatus.opphevet
    return PlanStatus.ukjent


_plan_provider: Optional[PlanProvider] = None


def get_plan_provider() -> PlanProvider:
    global _plan_provider
    if _plan_provider is None:
        _plan_provider = PlanProvider()
    return _plan_provider
