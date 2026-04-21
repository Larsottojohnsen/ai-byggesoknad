"""
AI Byggesøknad – FastAPI Backend
Main application entry point.
"""
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from routers import address, project, classify, documents

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-drevet byggesøknadsplattform for Norge",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(address.router)
app.include_router(project.router)
app.include_router(classify.router)
app.include_router(documents.router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "features": {
            "ai_classification": settings.feature_ai_classification,
            "pdf_generation": settings.feature_pdf_generation,
            "hazard_data": settings.feature_hazard_data,
            "plan_data": settings.feature_plan_data,
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Intern serverfeil", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
