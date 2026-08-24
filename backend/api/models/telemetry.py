"""
SatInsight AI — Telemetry Pydantic Models

Response schemas used by all data-layer routes.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Session / Dataset metadata
# ---------------------------------------------------------------------------


class DatasetMeta(BaseModel):
    session_id: str
    dataset_name: str
    row_count: int
    columns: list[str]
    created_at: float
    has_anomalies: bool = False


class DatasetListResponse(BaseModel):
    sessions: list[DatasetMeta]
    total: int


# ---------------------------------------------------------------------------
# Load / Upload response
# ---------------------------------------------------------------------------


class DatasetLoadResponse(BaseModel):
    session_id: str
    dataset_name: str
    row_count: int
    columns: list[str]
    warnings: list[str] = Field(default_factory=list)
    message: str


# ---------------------------------------------------------------------------
# Paginated data records
# ---------------------------------------------------------------------------


class TelemetryRecord(BaseModel):
    """One row of satellite telemetry. All fields optional to handle partial uploads."""
    timestamp: Optional[str] = None
    temperature: Optional[float] = None
    radiation: Optional[float] = None
    pressure: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    velocity: Optional[float] = None
    altitude: Optional[float] = None


class DataPageResponse(BaseModel):
    session_id: str
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    records: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


class ParameterStats(BaseModel):
    count: int
    mean: Optional[float]
    std: Optional[float]
    min: Optional[float]
    max: Optional[float]
    q1: Optional[float]
    median: Optional[float]
    q3: Optional[float]
    iqr: Optional[float]
    missing_count: int


class DataStatsResponse(BaseModel):
    session_id: str
    dataset_name: str
    row_count: int
    parameters: dict[str, ParameterStats]


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


class DataPreviewResponse(BaseModel):
    session_id: str
    dataset_name: str
    row_count: int
    columns: list[str]
    preview_rows: list[dict[str, Any]]   # first N rows
    warnings: list[str] = Field(default_factory=list)
