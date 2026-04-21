"""
AddressProvider – adapter for Kartverket Adresse-API
Docs: https://api.kartverket.no/adresser/v1/
"""
import httpx
import structlog
from typing import List, Optional
from core.config import settings
from core.cache import cache_get, cache_set
from models.schemas import AddressSuggestion

logger = structlog.get_logger()

KARTVERKET_ADDRESS_URL = "https://ws.geonorge.no/adresser/v1/sok"
CACHE_TTL = 3600  # 1 hour


class AddressProvider:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def search(self, query: str, max_results: int = 8) -> List[AddressSuggestion]:
        """Search for addresses using Kartverket Adresse-API."""
        if len(query) < 3:
            return []

        cache_key = f"address:search:{query.lower().strip()}"
        cached = await cache_get(cache_key)
        if cached:
            return [AddressSuggestion(**item) for item in cached]

        try:
            response = await self.client.get(
                KARTVERKET_ADDRESS_URL,
                params={
                    "sok": query,
                    "treffPerSide": max_results,
                    "side": 0,
                    "utkoordsys": 4326,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            suggestions = []
            for addr in data.get("adresser", []):
                rep = addr.get("representasjonspunkt", {})
                lat = rep.get("lat") or rep.get("nord")
                lng = rep.get("lon") or rep.get("øst") or rep.get("lon")

                if not lat or not lng:
                    continue

                suggestion = AddressSuggestion(
                    id=f"{addr.get('kommunenummer', '')}-{addr.get('adressetekst', '')}",
                    text=addr.get("adressetekst", ""),
                    addressText=addr.get("adressetekst", ""),
                    municipality=addr.get("kommunenavn", ""),
                    municipalityNumber=addr.get("kommunenummer", ""),
                    postalCode=addr.get("postnummer"),
                    postalPlace=addr.get("poststed"),
                    lat=float(lat),
                    lng=float(lng),
                )
                suggestions.append(suggestion)

            await cache_set(cache_key, [s.model_dump() for s in suggestions], CACHE_TTL)
            return suggestions

        except httpx.HTTPError as e:
            logger.error("address_search_http_error", query=query, error=str(e))
            return []
        except Exception as e:
            logger.error("address_search_error", query=query, error=str(e))
            return []

    async def close(self):
        await self.client.aclose()


# Singleton
_address_provider: Optional[AddressProvider] = None


def get_address_provider() -> AddressProvider:
    global _address_provider
    if _address_provider is None:
        _address_provider = AddressProvider()
    return _address_provider
