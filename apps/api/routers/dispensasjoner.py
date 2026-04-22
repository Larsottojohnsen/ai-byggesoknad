"""
Dispensasjoner router — henter dispensasjonsvedtak fra eInnsyn og kommunenes postlister.
"""
import math
import asyncio
import httpx
from fastapi import APIRouter, Query
from models.schemas import ApiResponse

router = APIRouter(prefix="/dispensasjoner", tags=["dispensasjoner"])

EINNSYN_BASE = "https://einnsyn.no/api"
HEADERS = {
    "User-Agent": "AI-Byggesoknad/1.0 (https://github.com/Larsottojohnsen/ai-byggesoknad)",
    "Accept": "application/json",
}

# Keywords to search for by measure type
MEASURE_KEYWORDS: dict[str, list[str]] = {
    "garasje": ["garasje", "carport", "uthus"],
    "carport": ["carport", "garasje"],
    "tilbygg": ["tilbygg", "utvidelse", "påbygg"],
    "påbygg": ["påbygg", "tilbygg"],
    "veranda": ["veranda", "terrasse", "balkong"],
    "bruksendring": ["bruksendring"],
    "kjeller_innredning": ["kjeller", "loft", "innredning"],
    "loft_innredning": ["loft", "kjeller", "innredning"],
    "fasadeendring": ["fasadeendring", "fasade"],
    "støttemur": ["støttemur", "mur", "gjerde"],
    "tomtedeling": ["tomtedeling", "fradeling"],
    "annet": ["dispensasjon"],
}

def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in meters between two WGS84 points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def _search_einnsyn(
    municipality_number: str,
    keywords: list[str],
    limit: int = 20,
) -> list[dict]:
    """Search eInnsyn for dispensation cases in a municipality."""
    results = []
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        for keyword in keywords[:2]:  # limit to 2 keywords to avoid rate limiting
            try:
                # eInnsyn search API
                resp = await client.get(
                    f"{EINNSYN_BASE}/journalpost",
                    params={
                        "q": f"dispensasjon {keyword}",
                        "kommunenummer": municipality_number,
                        "size": limit,
                        "sort": "publisertDato:desc",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("_embedded", {}).get("journalpost", []) or data.get("hits", []) or []
                    results.extend(items)
            except Exception:
                pass
    return results


def _parse_einnsyn_item(item: dict) -> dict | None:
    """Parse an eInnsyn journalpost into our dispensasjon format."""
    try:
        title = item.get("offentligTittel") or item.get("tittel") or ""
        if not title:
            return None

        # Try to determine outcome from title
        title_lower = title.lower()
        if any(w in title_lower for w in ["innvilg", "godkjenn", "tillatelse", "vedtak om tillatelse"]):
            outcome = "innvilget"
        elif any(w in title_lower for w in ["avslå", "avslag", "avvist", "nektet"]):
            outcome = "avslatt"
        else:
            outcome = "ukjent"

        # Date
        date = item.get("publisertDato") or item.get("journaldato") or ""
        if date and "T" in date:
            date = date.split("T")[0]

        # URL
        id_ = item.get("id") or item.get("systemId") or ""
        url = f"https://einnsyn.no/journalpost/{id_}" if id_ else None

        # Address / location from title or beskrivelse
        address = ""
        beskrivelse = item.get("beskrivelse") or ""
        for part in [title, beskrivelse]:
            words = part.split()
            for i, w in enumerate(words):
                if any(c.isdigit() for c in w) and i > 0:
                    address = " ".join(words[max(0, i-2):i+2])
                    break
            if address:
                break

        return {
            "id": str(id_),
            "title": title[:120],
            "address": address or "Ukjent adresse",
            "date": date,
            "outcome": outcome,
            "description": beskrivelse[:200] if beskrivelse else "",
            "url": url,
            "distance": None,
        }
    except Exception:
        return None


@router.get("/nearby")
async def get_nearby_dispensasjoner(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    municipality_number: str = Query(..., description="Kommunenummer (4 siffer)"),
    measure_type: str = Query("annet", description="Tiltakstype"),
    radius: int = Query(1000, description="Søkeradius i meter"),
):
    """
    Henter dispensasjonsvedtak fra eInnsyn for en gitt kommune og tiltakstype.
    Returnerer saker sortert etter relevans.
    """
    keywords = MEASURE_KEYWORDS.get(measure_type, ["dispensasjon"])

    # Fetch from eInnsyn
    raw_items = await _search_einnsyn(municipality_number, keywords, limit=30)

    # Parse items
    dispensasjoner = []
    for item in raw_items:
        parsed = _parse_einnsyn_item(item)
        if parsed:
            dispensasjoner.append(parsed)

    # Remove duplicates by id
    seen = set()
    unique = []
    for d in dispensasjoner:
        if d["id"] not in seen:
            seen.add(d["id"])
            unique.append(d)

    # Sort: innvilget first, then by date
    def sort_key(d: dict):
        outcome_order = {"innvilget": 0, "ukjent": 1, "avslatt": 2}
        return (outcome_order.get(d["outcome"], 1), d["date"])

    unique.sort(key=sort_key)

    return ApiResponse(data=unique[:20])


@router.get("/stats")
async def get_dispensasjon_stats(
    municipality_number: str = Query(..., description="Kommunenummer"),
    measure_type: str = Query("annet", description="Tiltakstype"),
):
    """
    Returnerer statistikk om dispensasjoner i en kommune for en gitt tiltakstype.
    """
    keywords = MEASURE_KEYWORDS.get(measure_type, ["dispensasjon"])
    raw_items = await _search_einnsyn(municipality_number, keywords, limit=50)

    total = 0
    innvilget = 0
    avslatt = 0

    for item in raw_items:
        parsed = _parse_einnsyn_item(item)
        if parsed:
            total += 1
            if parsed["outcome"] == "innvilget":
                innvilget += 1
            elif parsed["outcome"] == "avslatt":
                avslatt += 1

    approval_rate = round(innvilget / total * 100) if total > 0 else None

    return ApiResponse(data={
        "total": total,
        "innvilget": innvilget,
        "avslatt": avslatt,
        "ukjent": total - innvilget - avslatt,
        "approval_rate_pct": approval_rate,
    })
