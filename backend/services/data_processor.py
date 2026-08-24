"""
SatInsight AI — Data Processor Service

Single source of truth for all CSV ingestion and preprocessing.
Both the upload flow and the sample-data flow pass through here.

Pipeline:
  1. parse_csv()       — read bytes/path into a raw DataFrame
  2. validate_columns()— ensure required telemetry columns exist
  3. parse_timestamps()— coerce the timestamp column to datetime
  4. fill_missing()    — forward-fill then median fallback per numeric column
  5. normalize()       — min-max scale numeric columns into [0, 1] (copy)
  6. compute_stats()   — per-column descriptive statistics
"""

import io
import math
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: list[str] = [
    "timestamp",
    "temperature",
    "radiation",
    "pressure",
    "battery_level",
    "signal_strength",
    "velocity",
    "altitude",
]

NUMERIC_COLUMNS: list[str] = [
    "temperature",
    "radiation",
    "pressure",
    "battery_level",
    "signal_strength",
    "velocity",
    "altitude",
]

# Columns that must never be negative after cleaning
NON_NEGATIVE_COLS: list[str] = ["radiation", "battery_level", "altitude"]

# Expected physical ranges for soft validation warnings (not hard errors)
PARAM_RANGES: dict[str, tuple[float, float]] = {
    "temperature": (-100.0, 200.0),
    "radiation": (0.0, 100.0),
    "pressure": (0.0, 200.0),
    "battery_level": (0.0, 100.0),
    "signal_strength": (-200.0, 0.0),
    "velocity": (0.0, 30.0),
    "altitude": (0.0, 100_000.0),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_csv(
    source: Union[bytes, str, Path],
    dataset_name: str = "dataset",
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """
    Full preprocessing pipeline.

    Parameters
    ----------
    source : bytes | str | Path
        Raw CSV bytes (from an upload) or a file path (for the sample data).
    dataset_name : str
        Label used in log messages.

    Returns
    -------
    raw_df : pd.DataFrame
        Cleaned, human-readable DataFrame (timestamps as strings, original scale).
    processed_df : pd.DataFrame
        Min-max normalised copy used by the ML layer.
    warnings : list[str]
        Non-fatal issues found during validation (e.g. out-of-range values).
    """
    df = _parse_csv(source)
    _validate_columns(df)
    df = _parse_timestamps(df)
    df, warnings = _fill_missing(df)
    df = _clip_non_negative(df)
    range_warnings = _check_ranges(df)
    warnings.extend(range_warnings)
    processed_df = _normalize(df)

    # Serialise timestamps to ISO strings so JSON conversion is trivial
    raw_df = df.copy()
    raw_df["timestamp"] = raw_df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return raw_df, processed_df, warnings


def compute_stats(raw_df: pd.DataFrame) -> dict:
    """
    Per-parameter descriptive statistics suitable for the /api/data/stats response.
    """
    stats: dict = {}
    for col in NUMERIC_COLUMNS:
        if col not in raw_df.columns:
            continue
        series = raw_df[col].dropna()
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        stats[col] = {
            "count": int(series.count()),
            "mean": _safe_float(series.mean()),
            "std": _safe_float(series.std()),
            "min": _safe_float(series.min()),
            "max": _safe_float(series.max()),
            "q1": _safe_float(q1),
            "median": _safe_float(series.median()),
            "q3": _safe_float(q3),
            "iqr": _safe_float(q3 - q1),
            "missing_count": int(raw_df[col].isna().sum()),
        }
    return stats


def df_to_records(df: pd.DataFrame, page: int, page_size: int) -> tuple[list[dict], int]:
    """
    Paginate a DataFrame and return plain JSON-serialisable records.

    Returns (records, total_rows).
    """
    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    slice_df = df.iloc[start:end]
    records = _df_to_safe_records(slice_df)
    return records, total


# ---------------------------------------------------------------------------
# Internal pipeline steps
# ---------------------------------------------------------------------------


def _parse_csv(source: Union[bytes, str, Path]) -> pd.DataFrame:
    """Read CSV from bytes or a file path."""
    try:
        if isinstance(source, bytes):
            df = pd.read_csv(io.BytesIO(source))
        else:
            df = pd.read_csv(source)
    except Exception as exc:
        # Import here to avoid circular dependency at module load
        from core.exceptions import InvalidCSVError
        raise InvalidCSVError(f"Could not parse file as CSV — {exc}") from exc

    if df.empty:
        from core.exceptions import InvalidCSVError
        raise InvalidCSVError("The CSV file contains no data rows.")

    # Normalise column names: strip whitespace, lowercase
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _validate_columns(df: pd.DataFrame) -> None:
    """Raise InvalidCSVError if any required column is absent."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        from core.exceptions import InvalidCSVError
        raise InvalidCSVError(
            f"Missing required columns: {missing}. "
            f"Expected: {REQUIRED_COLUMNS}"
        )


def _parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce the timestamp column to datetime; drop rows that can't be parsed."""
    df = df.copy()
    original_len = len(df)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    bad = df["timestamp"].isna().sum()
    if bad == original_len:
        from core.exceptions import InvalidCSVError
        raise InvalidCSVError(
            "The 'timestamp' column contains no parseable date values."
        )
    df = df.dropna(subset=["timestamp"]).reset_index(drop=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def _fill_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Handle missing values:
      1. Forward-fill (carries the last known value forward in time).
      2. Median fallback for any remaining NaN (e.g. leading NaN that can't be ffill'd).
    """
    df = df.copy()
    warnings: list[str] = []

    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue
        # Coerce to numeric first (handles stray strings like 'N/A')
        df[col] = pd.to_numeric(df[col], errors="coerce")
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            df[col] = df[col].ffill()
            # Remaining NaN after ffill → use column median
            remaining = int(df[col].isna().sum())
            if remaining > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
            warnings.append(
                f"Column '{col}': {n_missing} missing value(s) imputed via forward-fill / median."
            )

    return df, warnings


def _clip_non_negative(df: pd.DataFrame) -> pd.DataFrame:
    """Clip known non-negative columns to 0."""
    df = df.copy()
    for col in NON_NEGATIVE_COLS:
        if col in df.columns:
            df[col] = df[col].clip(lower=0.0)
    return df


def _check_ranges(df: pd.DataFrame) -> list[str]:
    """Soft-check physical plausibility. Returns warning strings (no exceptions)."""
    warnings: list[str] = []
    for col, (lo, hi) in PARAM_RANGES.items():
        if col not in df.columns:
            continue
        n_out = int(((df[col] < lo) | (df[col] > hi)).sum())
        if n_out > 0:
            warnings.append(
                f"Column '{col}': {n_out} value(s) outside expected range [{lo}, {hi}]. "
                "These may represent genuine anomalies."
            )
    return warnings


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Min-max normalise numeric columns into [0, 1].
    Returns a separate DataFrame (raw_df is not mutated).
    """
    norm_df = df.copy()
    for col in NUMERIC_COLUMNS:
        if col not in norm_df.columns:
            continue
        col_min = norm_df[col].min()
        col_max = norm_df[col].max()
        denom = col_max - col_min
        if denom == 0:
            norm_df[col] = 0.0
        else:
            norm_df[col] = (norm_df[col] - col_min) / denom
    return norm_df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(val) -> float:
    """Convert numpy scalar to Python float; return None if NaN/Inf."""
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 6)
    except (TypeError, ValueError):
        return None


def _df_to_safe_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame slice to JSON-safe dicts (handles NaN, numpy types)."""
    records = []
    for row in df.to_dict(orient="records"):
        clean = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean[k] = None
            elif isinstance(v, (np.integer,)):
                clean[k] = int(v)
            elif isinstance(v, (np.floating,)):
                clean[k] = float(v)
            else:
                clean[k] = v
        records.append(clean)
    return records
