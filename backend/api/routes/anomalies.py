"""
SatInsight AI — Anomaly Detection Routes

Endpoints:
  POST /api/analyze/{session_id}      — run Isolation Forest + Z-Score on a session
  GET  /api/anomalies/{session_id}    — paginated anomaly rows (Warning + Critical)
  GET  /api/anomalies/{session_id}/summary — risk count summary + per-param breakdown
"""

import math

from fastapi import APIRouter, Query, status

from api.models.anomaly import AnalyzeResponse, AnomalyListResponse, RiskCounts
from core.exceptions import NoDataLoadedError, SessionNotFoundError
from core.session import store
from services import anomaly_detector, insight_generator
from services.anomaly_detector import anomaly_rows_only, param_anomaly_counts, risk_counts
from services.data_processor import _df_to_safe_records

router = APIRouter(prefix="/api", tags=["Anomaly Detection"])


# ---------------------------------------------------------------------------
# Run detection
# ---------------------------------------------------------------------------

@router.post(
    "/analyze/{session_id}",
    response_model=AnalyzeResponse,
    summary="Run AI/ML anomaly detection on a loaded dataset",
    status_code=status.HTTP_200_OK,
)
async def run_analysis(session_id: str):
    """
    Trains an Isolation Forest on the session's normalised telemetry data and
    computes rolling Z-scores per parameter.  Results are stored back into the
    session so subsequent GET requests can retrieve them without re-running.

    Returns a risk summary immediately.  Use `GET /api/anomalies/{session_id}`
    to retrieve the full annotated row list.
    """
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    # Run the two-layer detection pipeline
    anomaly_df = anomaly_detector.detect(session)

    # Generate insight cards
    insights = insight_generator.generate(anomaly_df)
    insights_as_dicts = [c for c in insights]   # already dicts

    # Persist into the session for subsequent GET requests
    store.update_anomalies(
        session_id=session_id,
        anomaly_df=anomaly_df,
        insights=insights_as_dicts,
    )

    counts = risk_counts(anomaly_df)
    p_counts = param_anomaly_counts(anomaly_df)

    return AnalyzeResponse(
        session_id=session_id,
        dataset_name=session.dataset_name,
        row_count=len(anomaly_df),
        risk_counts=RiskCounts(**counts),
        param_anomaly_counts=p_counts,
        message=(
            f"Analysis complete. {counts['total_anomalies']} anomalies detected "
            f"({counts['Critical']} Critical, {counts['Warning']} Warning) "
            f"out of {counts['total_rows']} rows."
        ),
    )


# ---------------------------------------------------------------------------
# Paginated anomaly rows
# ---------------------------------------------------------------------------

@router.get(
    "/anomalies/{session_id}",
    response_model=AnomalyListResponse,
    summary="Get paginated anomaly rows for a session",
)
async def get_anomalies(
    session_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Rows per page"),
    risk: str = Query(
        default=None,
        description="Filter by risk level: 'Warning' | 'Critical' | omit for all anomalies",
    ),
):
    """
    Returns paginated anomaly rows (Warning and Critical only by default).
    Use `?risk=Critical` or `?risk=Warning` to filter further.
    Requires `POST /api/analyze/{session_id}` to have been called first.
    """
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    if session.anomaly_df is None:
        raise NoDataLoadedError()

    df = anomaly_rows_only(session.anomaly_df)

    # Optional risk filter
    if risk in ("Warning", "Critical"):
        df = df[df["risk_level"] == risk]

    total = len(df)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end].reset_index(drop=False)   # keep original row_index

    # Convert to JSON-safe records
    records = []
    for _, row in page_df.iterrows():
        rec = row.to_dict()
        # Rename the index column
        rec["row_index"] = int(rec.pop("index", rec.get("row_index", 0)))
        # Parse anomaly_params from comma string back to list
        params_str = str(rec.get("anomaly_params", ""))
        rec["anomaly_params"] = [p.strip() for p in params_str.split(",") if p.strip()]
        # Clean nan / numpy types
        clean = {}
        for k, v in rec.items():
            import math as _math
            import numpy as _np
            if isinstance(v, float) and (_math.isnan(v) or _math.isinf(v)):
                clean[k] = None
            elif isinstance(v, _np.integer):
                clean[k] = int(v)
            elif isinstance(v, _np.floating):
                clean[k] = float(v)
            else:
                clean[k] = v
        records.append(clean)

    return AnomalyListResponse(
        session_id=session_id,
        page=page,
        page_size=page_size,
        total_anomalies=total,
        total_pages=total_pages,
        filter_risk=risk,
        anomalies=records,
    )


# ---------------------------------------------------------------------------
# Risk summary
# ---------------------------------------------------------------------------

@router.get(
    "/anomalies/{session_id}/summary",
    summary="Risk count summary and per-parameter anomaly breakdown",
)
async def get_anomaly_summary(session_id: str):
    """
    Returns counts by risk level and a per-parameter breakdown of how many
    rows each parameter contributed to anomalies.
    """
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    if session.anomaly_df is None:
        raise NoDataLoadedError()

    counts = risk_counts(session.anomaly_df)
    p_counts = param_anomaly_counts(session.anomaly_df)

    return {
        "session_id": session_id,
        "risk_counts": counts,
        "param_anomaly_counts": p_counts,
    }
