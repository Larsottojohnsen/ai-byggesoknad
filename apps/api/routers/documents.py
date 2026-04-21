from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
from services.document_service import generate_report
from models.schemas import ApiResponse

router = APIRouter(prefix="/documents", tags=["documents"])


class GenerateDocumentRequest(BaseModel):
    projectId: str
    type: str = "forhåndsvurdering"


@router.post("/generate")
async def generate_document(req: GenerateDocumentRequest):
    """Generate a document for a project."""
    try:
        result = await generate_report(req.projectId, req.type)
        return ApiResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dokumentgenerering feilet: {str(e)}")


@router.get("/download/{filename}")
async def download_document(filename: str):
    """Download a generated document."""
    file_path = f"./uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
