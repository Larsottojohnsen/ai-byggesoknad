"""
Municipality Provider – Fase 3
Identifies the Norwegian municipality (kommune) from coordinates
using Kartverket's reverse-geocoding API, then loads
municipality-specific rules from YAML files.
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
import yaml
import structlog

logger = structlog.get_logger()

# Path to kommuner YAML rules directory
KOMMUNER_DIR = Path(__file__).parent.parent / "rules" / "kommuner"

# Cache: kommunenr → rules dict
_rules_cache: Dict[str, Dict[str, Any]] = {}

# Cache: (lat, lng) rounded to 3 decimals → kommuneinfo
_geo_cache: Dict[str, Dict[str, Any]] = {}


async def identify_municipality(lat: float, lng: float) -> Dict[str, Any]:
    """
    Identify the Norwegian municipality from coordinates.
    Uses Kartverket's stedsnavn/punkt API for reverse geocoding.
    Returns dict with kommunenr, kommunenavn, fylke.
    """
    cache_key = f"{round(lat, 3)},{round(lng, 3)}"
    if cache_key in _geo_cache:
        return _geo_cache[cache_key]

    result = {
        "kommunenr": None,
        "kommunenavn": "Ukjent",
        "fylke": "Ukjent",
        "source": "fallback",
    }

    # NOTE: The kommuneinfo API moved in Dec 2023 from ws.geonorge.no to api.kartverket.no
    # Try new endpoint first, then fall back to old one
    endpoints = [
        "https://api.kartverket.no/kommuneinfo/v1/punkt",
        "https://ws.geonorge.no/kommuneinfo/v1/punkt",
    ]

    for url in endpoints:
        try:
            params = {"nord": lat, "ost": lng, "koordsys": 4326}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    result = {
                        "kommunenr": data.get("kommunenummer", ""),
                        "kommunenavn": data.get("kommunenavn", "Ukjent"),
                        "fylke": data.get("fylkesnavn", "Ukjent"),
                        "source": "kartverket",
                    }
                    logger.info(
                        "municipality_identified",
                        kommunenr=result["kommunenr"],
                        kommunenavn=result["kommunenavn"],
                        url=url,
                    )
                    break
                else:
                    logger.warning("municipality_api_error", status=resp.status_code, url=url)
        except Exception as e:
            logger.warning("municipality_lookup_failed", error=str(e), url=url)

    _geo_cache[cache_key] = result
    return result


def load_kommune_rules(kommunenr: str) -> Optional[Dict[str, Any]]:
    """
    Load municipality-specific rules from YAML file.
    Returns None if no rules file exists for the municipality.
    """
    if kommunenr in _rules_cache:
        return _rules_cache[kommunenr]

    # Try exact match first, then prefix match
    candidates = list(KOMMUNER_DIR.glob(f"{kommunenr}_*.yaml"))
    if not candidates:
        # Try 4-digit prefix (some municipalities changed numbers)
        candidates = list(KOMMUNER_DIR.glob(f"{kommunenr[:4]}_*.yaml"))

    if not candidates:
        logger.debug("no_kommune_rules", kommunenr=kommunenr)
        return None

    try:
        with open(candidates[0], "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
        _rules_cache[kommunenr] = rules
        logger.info("kommune_rules_loaded", kommunenr=kommunenr, file=candidates[0].name)
        return rules
    except Exception as e:
        logger.warning("kommune_rules_load_failed", kommunenr=kommunenr, error=str(e))
        return None


def get_kommune_contact(kommunenr: str) -> Dict[str, str]:
    """Get contact information for a municipality."""
    rules = load_kommune_rules(kommunenr)
    if rules and "kontakt" in rules:
        return rules["kontakt"]
    return {
        "url": "https://www.kommunekart.com",
        "merknad": "Kontakt din kommune for byggesaksbehandling",
    }


def get_kommune_fees(kommunenr: str) -> Optional[Dict[str, Any]]:
    """Get fee schedule for a municipality."""
    rules = load_kommune_rules(kommunenr)
    if rules and "gebyrer" in rules:
        return rules["gebyrer"]
    return None


def get_kommune_extra_docs(kommunenr: str) -> list:
    """Get extra document requirements for a municipality."""
    rules = load_kommune_rules(kommunenr)
    if rules and "ekstra_dokumentkrav" in rules:
        return rules["ekstra_dokumentkrav"]
    return []


def get_kommune_special_measures(kommunenr: str, measure_type: str) -> Optional[Dict[str, Any]]:
    """Get municipality-specific rules for a measure type."""
    rules = load_kommune_rules(kommunenr)
    if not rules or "saerlige_tiltak" not in rules:
        return None
    for tiltak in rules["saerlige_tiltak"]:
        if tiltak.get("type") == measure_type:
            return tiltak
    return None


def list_supported_municipalities() -> list:
    """List all municipalities with rules files."""
    result = []
    for f in sorted(KOMMUNER_DIR.glob("*.yaml")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = yaml.safe_load(fp)
            result.append({
                "kommunenr": data.get("kommune_nr"),
                "kommunenavn": data.get("kommune_navn"),
                "fylke": data.get("fylke"),
            })
        except Exception:
            pass
    return result
