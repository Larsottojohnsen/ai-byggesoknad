from fastapi import APIRouter
from pydantic import BaseModel
from services.ai_orchestrator import get_ai_orchestrator
from models.schemas import ApiResponse

router = APIRouter(prefix="/classify", tags=["classify"])


class ClassifyRequest(BaseModel):
    text: str


@router.post("")
async def classify_measure(req: ClassifyRequest):
    """Classify a building measure from free text description."""
    orchestrator = get_ai_orchestrator()
    classification = await orchestrator.classify_measure(req.text)
    return ApiResponse(data=classification)
