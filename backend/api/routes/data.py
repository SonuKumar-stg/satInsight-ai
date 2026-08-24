"""
SatInsight AI — Data Routes

Endpoints:
  GET  /api/sample                — load the bundled sample satellite dataset
  POST /api/upload                — upload a custom CSV file
  GET  /api/sessions              — list all active sessions
  GET  /api/data/{session_id}     — paginated telemetry records
  GET  /api/data/{session_id}/preview  — first N rows + column metadata
  GET  /api/data/{session_id}/stats   — per-parameter descriptive statistics
"""

import math
from pathlib import Path

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import JSONResponse

from api.models.telemetry import (
    DataPageResponse,
    DataPreviewResponse,
    DatasetListResponse,
    DatasetLoadResponse,
    DataStatsResponse,
)
from core.config import settings
from core.exceptions import FileTooLargeError, SessionNotFoundError
from core.session import store
from services.data_processor import compute_stats, df_to_records, process_csv

router = APIRouter(prefix="/api", tags=["Data"])

# Absolute path to the bundled sample CSV
_SAMPLE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_satellite.csv"


# ---------------------------------------------------------------------------
# Sample dataset
# ---------------------------------------------------------------------------


@router.get(
    "/sample",
    response_model=DatasetLoadResponse,
    summary="Load the bundled sample satellite dataset",
    status_code=status.HTTP_200_OK,
)
async def load_sample():
    """
    Reads the bundled `sample_satellite.csv` (600 rows, 8 parameters, 10 anomaly windows),
    runs the full preprocessing pipeline, stores it in the session store, and returns
    the session metadata.  Use the returned `session_id` for all subsequent requests.
    """
    raw_df, processed_df, warnings = process_csv(
        _SAMPLE_PATH,
        dataset_name="sample_satellite.csv",
    )
    session = store.create(
        dataset_name="sample_satellite.csv",
        raw_df=raw_df,
        processed_df=processed_df,
    )
    return DatasetLoadResponse(
        session_id=session.session_id,
        dataset_name=session.dataset_name,
        row_count=session.row_count,
        columns=session.column_names,
        warnings=warnings,
        message=f"Sample dataset loaded successfully. {session.row_count} rows ready.",
    )


# ---------------------------------------------------------------------------
# CSV upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=DatasetLoadResponse,
    summary="Upload a custom satellite telemetry CSV",
    status_code=status.HTTP_201_CREATED,
)
async def upload_csv(file: UploadFile = File(..., description="Satellite telemetry CSV file")):
    """
    Accepts a CSV file upload.  Required columns:
    `timestamp`, `temperature`, `radiation`, `pressure`,
    `battery_level`, `signal_strength`, `velocity`, `altitude`.

    Returns a `session_id` to use in all subsequent data requests.
    """
    # Size guard (read into memory — reasonable for MVP)
    raw_bytes = await file.read()
    max_bytes = settings.max_upload_bytes
    if len(raw_bytes) > max_bytes:
        raise FileTooLargeError(max_mb=max_bytes // (1024 * 1024))

    filename = file.filename or "upload.csv"
    raw_df, processed_df, warnings = process_csv(raw_bytes, dataset_name=filename)

    # Row limit guard
    if len(raw_df) > settings.max_upload_rows:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "detail": f"File contains {len(raw_df)} rows, which exceeds the "
                          f"{settings.max_upload_rows:,} row limit."
            },
        )

    session = store.create(
        dataset_name=filename,
        raw_df=raw_df,
        processed_df=processed_df,
    )
    return DatasetLoadResponse(
        session_id=session.session_id,
        dataset_name=session.dataset_name,
        row_count=session.row_count,
        columns=session.column_names,
        warnings=warnings,
        message=f"Dataset '{filename}' uploaded successfully. {session.row_count} rows ready.",
    )


# ---------------------------------------------------------------------------
# Session listing
# ---------------------------------------------------------------------------


@router.get(
    "/sessions",
    response_model=DatasetListResponse,
    summary="List all active dataset sessions",
)
async def list_sessions():
    """Returns all sessions currently held in the in-memory store."""
    sessions = store.list_sessions()
    return DatasetListResponse(
        sessions=sessions,
        total=len(sessions),
    )


# ---------------------------------------------------------------------------
# Paginated records
# ---------------------------------------------------------------------------


@router.get(
    "/data/{session_id}",
    response_model=DataPageResponse,
    summary="Get paginated telemetry records for a session",
)
async def get_data(
    session_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Rows per page"),
):
    """
    Returns a page of telemetry rows for the given session.
    Supports `page` and `page_size` query parameters.
    """
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    records, total = df_to_records(session.raw_df, page=page, page_size=page_size)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return DataPageResponse(
        session_id=session_id,
        page=page,
        page_size=page_size,
        total_rows=total,
        total_pages=total_pages,
        records=records,
    )


# ---------------------------------------------------------------------------
# Preview (first N rows + column list)
# ---------------------------------------------------------------------------


@router.get(
    "/data/{session_id}/preview",
    response_model=DataPreviewResponse,
    summary="Preview the first N rows of a session's dataset",
)
async def get_preview(
    session_id: str,
    n: int = Query(default=10, ge=1, le=100, description="Number of rows to preview"),
):
    """Returns the first `n` rows and the full column list for a quick dataset inspection."""
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    preview_records, _ = df_to_records(session.raw_df, page=1, page_size=n)

    return DataPreviewResponse(
        session_id=session_id,
        dataset_name=session.dataset_name,
        row_count=session.row_count,
        columns=session.column_names,
        preview_rows=preview_records,
        warnings=[],
    )


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@router.get(
    "/data/{session_id}/stats",
    response_model=DataStatsResponse,
    summary="Per-parameter descriptive statistics for a session",
)
async def get_stats(session_id: str):
    """
    Returns min, max, mean, std, median, Q1, Q3, IQR and missing-value counts
    for each numeric telemetry parameter in the session.
    """
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    stats = compute_stats(session.raw_df)

    return DataStatsResponse(
        session_id=session_id,
        dataset_name=session.dataset_name,
        row_count=session.row_count,
        parameters=stats,
    )
