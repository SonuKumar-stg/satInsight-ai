"""
SatInsight AI — FastAPI Backend Entry Point
IBM AI Builders Challenge August 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.routes.data import router as data_router
from api.routes.anomalies import router as anomaly_router
from api.routes.insights import router as insight_router

app = FastAPI(
    title="SatInsight AI",
    description="AI-powered Satellite Data Analysis Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — origins driven by settings (configurable via .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(data_router)
app.include_router(anomaly_router)
app.include_router(insight_router)

# Sub-Task 6 will add:
# from api.routes.reports import router as report_router
# app.include_router(report_router)


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint — returns service status."""
    return {
        "status": "ok",
        "service": "SatInsight AI",
        "version": "1.0.0",
    }
