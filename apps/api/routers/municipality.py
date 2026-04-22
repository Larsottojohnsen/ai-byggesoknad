"""
Municipality Router – Fase 3
Endpoints for municipality identification and kommune-specific rules.
"""
from fastapi import APIRouter, HTTPException, Query
from models.schemas import ApiResponse
from providers.municipality_provider import (
    identify_municipality,
    load_kommune_rules,
    get_kommune_contact,
    get_kommune_fees,
    get_kommune_extra_docs,
    list_supported_municipalities,
)

router = APIRouter(prefix="/municipality", tags=["municipality"])


@router.get("/identify")
async def identify_from_coordinates(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lng: float = Query(..., description="Longitude (WGS84)"),
):
    """
    Identify Norwegian municipality from coordinates.
    Returns kommunenr, kommunenavn, fylke and available rules.
    """
    info = await identify_municipality(lat, lng)
    kommunenr = info.get("kommunenr", "")

    # Enrich with rules availability
    rules = load_kommune_rules(kommunenr) if kommunenr else None
    info["hasKommuneRules"] = rules is not None
    info["kontakt"] = get_kommune_contact(kommunenr) if kommunenr else {}
    info["ekstraKrav"] = get_kommune_extra_docs(kommunenr) if kommunenr else []

    fees = get_kommune_fees(kommunenr) if kommunenr else None
    if fees:
        info["gebyrer"] = fees

    return ApiResponse(data=info)


@router.get("/rules/{kommunenr}")
async def get_kommune_rules(kommunenr: str):
    """Get full municipality-specific rules for a given kommunenr."""
    rules = load_kommune_rules(kommunenr)
    if not rules:
        raise HTTPException(
            status_code=404,
            detail=f"Ingen kommunespesifikke regler funnet for kommunenr {kommunenr}. "
                   "Nasjonale regler gjelder.",
        )
    return ApiResponse(data=rules)


@router.get("/supported")
async def get_supported_municipalities():
    """List all municipalities with dedicated rules files."""
    return ApiResponse(data=list_supported_municipalities())
