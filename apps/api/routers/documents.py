from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from services.document_service import generate_report
from services.document_generator import get_document_generator
from services.analysis_service import get_project, get_analysis_result
from models.schemas import ApiResponse

router = APIRouter(prefix="/documents", tags=["documents"])


class GenerateDocumentRequest(BaseModel):
    projectId: str
    type: str = "forhåndsvurdering"


class GenerateTextDocumentRequest(BaseModel):
    projectId: str
    ownerName: Optional[str] = "[Eiers navn]"
    ownerAddress: Optional[str] = "[Eiers adresse]"


@router.post("/generate")
async def generate_document(req: GenerateDocumentRequest):
    """Generate a PDF report for a project."""
    try:
        result = await generate_report(req.projectId, req.type)
        return ApiResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dokumentgenerering feilet: {str(e)}")


@router.post("/tiltaksbeskrivelse")
async def generate_tiltaksbeskrivelse(req: GenerateTextDocumentRequest):
    """
    AI Agent 3: Generate a formal tiltaksbeskrivelse (measure description).
    Required document for søknadspliktige tiltak.
    """
    project = await get_project(req.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

    analysis = await get_analysis_result(req.projectId)
    analysis_dict = analysis.model_dump() if analysis else None

    generator = get_document_generator()
    text = await generator.generate_tiltaksbeskrivelse(
        project=project.model_dump(),
        analysis=analysis_dict,
    )
    return ApiResponse(data={
        "type": "tiltaksbeskrivelse",
        "projectId": req.projectId,
        "content": text,
        "aiGenerated": True,
    })


@router.post("/nabovarsel")
async def generate_nabovarsel(req: GenerateTextDocumentRequest):
    """
    AI Agent 4: Generate a nabovarsel (neighbour notification letter).
    Required for søknadspliktige tiltak per PBL § 21-3.
    """
    project = await get_project(req.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

    analysis = await get_analysis_result(req.projectId)
    analysis_dict = analysis.model_dump() if analysis else None

    generator = get_document_generator()
    text = await generator.generate_nabovarsel(
        project=project.model_dump(),
        analysis=analysis_dict,
        owner_name=req.ownerName or "[Eiers navn]",
        owner_address=req.ownerAddress or "[Eiers adresse]",
    )
    return ApiResponse(data={
        "type": "nabovarsel",
        "projectId": req.projectId,
        "content": text,
        "aiGenerated": True,
        "legalBasis": "PBL § 21-3, SAK10 § 5-2",
    })


@router.post("/soknadsutkast")
async def generate_soknadsutkast(req: GenerateTextDocumentRequest):
    """
    AI Agent 5: Generate a søknadsutkast (application draft) with structured guidance.
    """
    project = await get_project(req.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")

    analysis = await get_analysis_result(req.projectId)
    analysis_dict = analysis.model_dump() if analysis else None

    generator = get_document_generator()
    text = await generator.generate_soknadsutkast(
        project=project.model_dump(),
        analysis=analysis_dict,
    )
    return ApiResponse(data={
        "type": "soknadsutkast",
        "projectId": req.projectId,
        "content": text,
        "aiGenerated": True,
    })


@router.get("/download/{filename}")
async def download_document(filename: str):
    """Download a generated document."""
    file_path = f"./uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
