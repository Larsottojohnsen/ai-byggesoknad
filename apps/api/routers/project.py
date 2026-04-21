from fastapi import APIRouter, HTTPException
from models.schemas import CreateProjectRequest, ApiResponse
from services.analysis_service import (
    create_project,
    analyze_project,
    get_project,
    get_analysis_result,
)

router = APIRouter(prefix="/project", tags=["project"])


@router.post("/create")
async def create_new_project(req: CreateProjectRequest):
    """Create a new project."""
    project = await create_project(req)
    return ApiResponse(data=project)


@router.post("/{project_id}/analyze")
async def run_analysis(project_id: str):
    """Run full analysis pipeline for a project."""
    try:
        result = await analyze_project(project_id)
        return ApiResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyse feilet: {str(e)}")


@router.get("/{project_id}")
async def get_project_details(project_id: str):
    """Get project details."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")
    return ApiResponse(data=project)


@router.get("/{project_id}/results")
async def get_project_results(project_id: str):
    """Get analysis results for a project."""
    result = await get_analysis_result(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analyseresultat ikke funnet")
    return ApiResponse(data=result)
