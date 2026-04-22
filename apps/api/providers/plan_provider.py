"""
PlanProvider – adapter for Kartverket arealplaner REST API
Uses arealplaner.kartverket.no/api/arealplan/v1 for reguleringsplan lookup.
"""
import httpx
import structlog
from typing import Optional, List, Dict, Any
from core.cache import cache_get, cache_set
from models.schemas import PlanLayerResult, PlanStatus

logger = structlog.get_logger()

# Kartverket arealplaner REST API (confirmed working)
AREALPLANER_BASE = "https://arealplaner.kartverket.no/api/arealplan/v1"
CACHE_TTL = 21600  # 6 hours


class PlanProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def lookup(self, lat: float, lng: float, kommunenr: str = None) -> Optional[PlanLayerResult]:
        """Look up plan layers for given coordinates."""
        cache_key = f"plan:{lat:.4f}:{lng:.4f}"
        cached = await cache_get(cache_key)
        if cached:
            return PlanLayerResult(**cached)

        result = None

        # Try arealplaner.kartverket.no if we have kommunenr
        if kommunenr and kommunenr != "0000":
            result = await self._try_arealplaner_api(lat, lng, kommunenr)

        if not result:
            result = self._create_unknown_plan()

        await cache_set(cache_key, result.model_dump(), CACHE_TTL)
        return result

    async def _try_arealplaner_api(self, lat: float, lng: float, kommunenr: str) -> Optional[PlanLayerResult]:
        """Try Kartverket arealplaner REST API."""
        try:
            response = await self.client.get(
                f"{AREALPLANER_BASE}/planomrader",
                params={
                    "kommunenummer": kommunenr,
                    "koordinatSytem": "4326",
                    "nord": lat,
                    "ost": lng,
                },
                timeout=12.0,
            )

            if response.status_code == 200:
                data = response.json()
                # Response can be a list or have a 'planomrader' key
                plans = data if isinstance(data, list) else data.get("planomrader", data.get("features", []))
                if plans and len(plans) > 0:
                    # Pick the most specific plan (reguleringsplan over kommuneplan)
                    best_plan = self._pick_best_plan(plans)
                    if best_plan:
                        result = self._parse_arealplaner_plan(best_plan)
                        logger.info("plan_found", kommunenr=kommunenr, plan_id=result.planId)
                        return result
                else:
                    logger.info("plan_no_results", kommunenr=kommunenr, lat=lat, lng=lng)

        except Exception as e:
            logger.warning("plan_arealplaner_error", lat=lat, lng=lng, kommunenr=kommunenr, error=str(e))

        return None

    def _pick_best_plan(self, plans: list) -> Optional[Dict]:
        """Pick the most specific plan from a list."""
        if not plans:
            return None

        # Prefer reguleringsplan over kommuneplan
        for plan in plans:
            plantype = str(plan.get("plantype", plan.get("planType", ""))).lower()
            if "regulering" in plantype or "detaljregulering" in plantype:
                return plan

        # Fall back to first plan
        return plans[0]

    def _parse_arealplaner_plan(self, plan: Dict[str, Any]) -> PlanLayerResult:
        """Parse a Kartverket arealplaner plan object into PlanLayerResult."""
        # Determine plan status
        plantype = str(plan.get("plantype", plan.get("planType", ""))).lower()
        planstatus_raw = str(plan.get("planstatus", plan.get("planStatus", ""))).lower()

        if "regulering" in plantype or "detaljregulering" in plantype:
            status = PlanStatus.regulert
        elif "kommuneplan" in plantype or "kommunedelplan" in plantype:
            status = PlanStatus.kommuneplan
        else:
            status = PlanStatus.ukjent

        # Extract arealformål
        areal_formal = (
            plan.get("arealformål") or
            plan.get("arealFormål") or
            plan.get("formål") or
            plan.get("planformål") or
            "ukjent"
        )
        if isinstance(areal_formal, str):
            areal_formal = areal_formal.lower()

        # Extract hensynssoner
        hensynssoner = []
        hs = plan.get("hensynssoner", plan.get("hensynssone", []))
        if isinstance(hs, str):
            hensynssoner = [hs]
        elif isinstance(hs, list):
            hensynssoner = hs

        # Plan ID and name
        plan_id = (
            plan.get("planidentifikasjon") or
            plan.get("planId") or
            plan.get("planid") or
            plan.get("id")
        )
        plan_name = (
            plan.get("plannavn") or
            plan.get("planNavn") or
            plan.get("name") or
            plan.get("planname")
        )

        # Utnyttelsesgrad
        utnyttelsesgrad = (
            plan.get("utnyttelsesgrad") or
            plan.get("bya") or
            plan.get("BYA")
        )

        return PlanLayerResult(
            planId=str(plan_id) if plan_id else None,
            planName=plan_name,
            planStatus=status,
            arealFormål=areal_formal or "ukjent",
            hensynssoner=hensynssoner,
            byggegrense=plan.get("byggegrense"),
            utnyttelsesgrad=float(utnyttelsesgrad) if utnyttelsesgrad else None,
            planUrl=plan.get("planUrl") or plan.get("planurl"),
            geometry=None,
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
