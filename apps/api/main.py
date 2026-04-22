"""
AI Byggesøknad – FastAPI Backend
Main application entry point.
Fase 3: + municipality router, rate limiting, SSE progress stream
"""
import time
import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from core.config import settings
from routers import address, project, classify, documents, municipality

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

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting (simple in-memory token bucket) ────────────────────────────
_rate_store: dict = defaultdict(lambda: {"count": 0, "window_start": time.time()})
RATE_LIMIT = 60        # requests per window
RATE_WINDOW = 60       # seconds
RATE_LIMIT_HEAVY = 10  # for AI/analysis endpoints


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple sliding-window rate limiter."""
    # Skip rate limiting for health and docs
    if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    ip = _get_client_ip(request)
    now = time.time()
    bucket = _rate_store[ip]

    # Reset window
    if now - bucket["window_start"] > RATE_WINDOW:
        bucket["count"] = 0
        bucket["window_start"] = now

    # Heavier limit for AI endpoints
    is_heavy = any(
        request.url.path.startswith(p)
        for p in ["/project/", "/classify", "/documents/tiltaksbeskrivelse",
                  "/documents/nabovarsel", "/documents/soknadsutkast"]
    )
    limit = RATE_LIMIT_HEAVY if is_heavy else RATE_LIMIT

    bucket["count"] += 1
    if bucket["count"] > limit:
        logger.warning("rate_limit_exceeded", ip=ip, path=request.url.path)
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "For mange forespørsler. Prøv igjen om litt.",
                "retry_after": int(RATE_WINDOW - (now - bucket["window_start"])),
            },
            headers={"Retry-After": str(int(RATE_WINDOW - (now - bucket["window_start"])))},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - bucket["count"]))
    return response


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(address.router)
app.include_router(project.router)
app.include_router(classify.router)
app.include_router(documents.router)
app.include_router(municipality.router)


# ── SSE: Analysis progress stream ─────────────────────────────────────────────
# In-memory progress store: project_id → list of progress events
_progress_store: dict = {}


def emit_progress(project_id: str, step: str, message: str, pct: int):
    """Called by analysis_service to emit progress events."""
    if project_id not in _progress_store:
        _progress_store[project_id] = []
    _progress_store[project_id].append({
        "step": step,
        "message": message,
        "pct": pct,
        "done": pct >= 100,
    })


async def _progress_generator(project_id: str) -> AsyncGenerator[str, None]:
    """SSE generator that streams progress events for a project."""
    sent_idx = 0
    timeout = 120  # max 2 minutes
    elapsed = 0
    interval = 0.5

    while elapsed < timeout:
        events = _progress_store.get(project_id, [])
        while sent_idx < len(events):
            evt = events[sent_idx]
            yield f"data: {json.dumps(evt)}\n\n"
            sent_idx += 1
            if evt.get("done"):
                return
        await asyncio.sleep(interval)
        elapsed += interval

    yield f"data: {json.dumps({'step': 'timeout', 'message': 'Tidsavbrudd', 'pct': 0, 'done': True})}\n\n"


@app.get("/project/{project_id}/progress")
async def analysis_progress_stream(project_id: str):
    """
    Server-Sent Events stream for analysis progress.
    Connect before calling /project/{id}/analyze to receive live updates.
    """
    return StreamingResponse(
        _progress_generator(project_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Health ────────────────────────────────────────────────────────────────────
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
            "municipality_rules": True,
            "rate_limiting": True,
            "sse_progress": True,
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Intern serverfeil", "detail": str(exc)},
    )


# ── Startup: run Alembic migrations ─────────────────────────────────────────
@app.on_event("startup")
async def run_migrations():
    """Run Alembic migrations on startup if DATABASE_URL is configured."""
    import os
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url or db_url.startswith("postgresql+asyncpg://localhost"):
        logger.info("skipping_migrations", reason="no production DATABASE_URL")
        return
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        # Use sync URL for Alembic
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql://", "postgresql://")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("migrations_complete")
    except Exception as e:
        logger.warning("migrations_skipped", error=str(e))


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
