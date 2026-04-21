from fastapi import APIRouter, Query, HTTPException
from providers.address_provider import get_address_provider
from models.schemas import ApiResponse

router = APIRouter(prefix="/address", tags=["address"])


@router.get("/search")
async def search_address(q: str = Query(..., min_length=3, description="Søketekst for adresse")):
    """Search for Norwegian addresses using Kartverket Adresse-API."""
    provider = get_address_provider()
    suggestions = await provider.search(q)
    return ApiResponse(data=suggestions)
