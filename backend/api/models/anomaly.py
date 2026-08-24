"""
SatInsight AI — Anomaly Pydantic Models

Response schemas for anomaly detection and AI insight endpoints.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Individual anomaly row
# ---------------------------------------------------------------------------

class AnomalyRow(BaseModel):
    """One telemetry row annotated with anomaly scores and risk level."""
    row_index: int
    timestamp: Optional[str] = None
    temperature: Optional[float] = None
    radiation: Optional[float] = None
    pressure: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    velocity: Optional[float] = None
    altitude: Optional[float] = None
    if_score: float
    max_zscore: float
    risk_level: str                 # "Normal" | "Warning" | "Critical"
    anomaly_params: list[str]       # parameters that breached Z-score threshold


# ---------------------------------------------------------------------------
# Analyze response
# ---------------------------------------------------------------------------

class RiskCounts(BaseModel):
    Normal: int
    Warning: int
    Critical: int
    total_anomalies: int
    total_rows: int


class AnalyzeResponse(BaseModel):
    session_id: str
    dataset_name: str
    row_count: int
    risk_counts: RiskCounts
    param_anomaly_counts: dict[str, int]
    message: str


# ---------------------------------------------------------------------------
# Anomalies list (paginated)
# ---------------------------------------------------------------------------

class AnomalyListResponse(BaseModel):
    session_id: str
    page: int
    page_size: int
    total_anomalies: int
    total_pages: int
    filter_risk: Optional[str]      # None = all, "Warning", "Critical"
    anomalies: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Insight card
# ---------------------------------------------------------------------------

class InsightCard(BaseModel):
    id: str
    title: str
    description: str
    severity: str                   # "info" | "warning" | "critical"
    parameter: str                  # primary affected parameter or "multi"
    value_range: str
    recommended_action: str
    row_start: int
    row_end: int
    event_rows: int


class InsightsResponse(BaseModel):
    session_id: str
    dataset_name: str
    total_insights: int
    insights: list[InsightCard]
    analysis_run: bool              # False if analyze hasn't been called yet
