"""
SatInsight AI — Insights Routes

Endpoints:
  GET /api/insights/{session_id}  — AI-generated insight cards for a session
"""

from fastapi import APIRouter, status

from api.models.anomaly import InsightCard, InsightsResponse
from core.exceptions import NoDataLoadedError, SessionNotFoundError
from core.session import store
from services import insight_generator

router = APIRouter(prefix="/api", tags=["AI Insights"])


@router.get(
    "/insights/{session_id}",
    response_model=InsightsResponse,
    summary="Get AI-generated insight cards for a session",
    status_code=status.HTTP_200_OK,
)
async def get_insights(session_id: str):
    """
    Returns the pre-computed insight cards from the last `POST /api/analyze` call.
    Each card contains a title, AI-generated description, affected parameter,
    severity level, value range, and a recommended action.

    Returns 400 if analysis has not been run yet.
    """
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    if session.anomaly_df is None:
        raise NoDataLoadedError()

    # Use cached insights if available; else re-generate from anomaly_df
    raw_insights = session.insights
    if raw_insights is None:
        raw_insights = insight_generator.generate(session.anomaly_df)
        store.update_anomalies(
            session_id=session_id,
            anomaly_df=session.anomaly_df,
            insights=raw_insights,
        )

    cards = [InsightCard(**c) for c in raw_insights]

    return InsightsResponse(
        session_id=session_id,
        dataset_name=session.dataset_name,
        total_insights=len(cards),
        insights=cards,
        analysis_run=True,
    )


@router.get(
    "/insights/{session_id}/status",
    summary="Check whether analysis has been run for a session",
)
async def get_insight_status(session_id: str):
    """Lightweight check — no analysis required."""
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    return {
        "session_id": session_id,
        "analysis_run": session.anomaly_df is not None,
        "insight_count": len(session.insights) if session.insights else 0,
    }
