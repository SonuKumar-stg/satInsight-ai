"""
SatInsight AI — Anomaly Detector Service

Two-layer detection pipeline:

  Layer 1 — Multivariate (Isolation Forest)
    Trains on the full normalised feature matrix.
    Produces a per-row anomaly score in [-1, 0].
    Lower (more negative) score = more anomalous.

  Layer 2 — Univariate (rolling Z-Score, window=50)
    Computes per-parameter Z-scores relative to a 50-row rolling window
    to capture orbital-period drift rather than the global mean.

Risk classification (per plan):
    Critical : IF score < -0.3  OR  any |Z-score| > 3.5
    Warning  : IF score < -0.1  OR  any |Z-score| > 2.5
    Normal   : everything else

Public interface
----------------
    detect(session_data)  →  anomaly_df : pd.DataFrame
        Columns added to a copy of raw_df:
          if_score      float   Isolation Forest anomaly score
          max_zscore    float   max |Z-score| across all parameters for that row
          risk_level    str     "Normal" | "Warning" | "Critical"
          anomaly_params list[str]  parameters that exceeded Z-score thresholds
"""

import warnings
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from core.config import settings
from services.data_processor import NUMERIC_COLUMNS

if TYPE_CHECKING:
    from core.session import SessionData

# ---------------------------------------------------------------------------
# Thresholds (mirror the plan exactly)
# ---------------------------------------------------------------------------

IF_CRITICAL = -0.3
IF_WARNING  = -0.1
Z_CRITICAL  = 3.5
Z_WARNING   = 2.5
Z_WINDOW    = 50      # rolling window for Z-score (≈ 1 orbital period at 30s cadence)


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def detect(session_data: "SessionData") -> pd.DataFrame:
    """
    Run the two-layer anomaly detection pipeline on a session's data.

    Parameters
    ----------
    session_data : SessionData
        Must have .raw_df (original scale) and .processed_df (normalised).

    Returns
    -------
    anomaly_df : pd.DataFrame
        Copy of raw_df with four extra columns:
        if_score, max_zscore, risk_level, anomaly_params.
    """
    raw_df       = session_data.raw_df.copy()
    processed_df = session_data.processed_df

    feature_cols = [c for c in NUMERIC_COLUMNS if c in processed_df.columns]
    X = processed_df[feature_cols].values

    # ── Layer 1: Isolation Forest ──────────────────────────────────────────
    contamination = min(max(settings.anomaly_contamination, 0.01), 0.5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf = IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=42,
            n_jobs=1,
        )
        clf.fit(X)

    # decision_function returns scores in roughly [-0.5, 0.5];
    # negative means "more anomalous" — matches our threshold convention.
    if_scores: np.ndarray = clf.decision_function(X)

    # ── Layer 2: Rolling Z-Score per parameter ─────────────────────────────
    zscore_df = _rolling_zscore(raw_df, feature_cols, window=Z_WINDOW)

    max_zscore = zscore_df.abs().max(axis=1).values

    # Which parameters breached the Warning Z-score threshold (per row)?
    flagged_params: list[list[str]] = []
    for i in range(len(raw_df)):
        row_flags = [
            col for col in feature_cols
            if abs(zscore_df.iloc[i][col]) > Z_WARNING
        ]
        flagged_params.append(row_flags)

    # ── Risk classification ────────────────────────────────────────────────
    risk_levels = _classify(if_scores, max_zscore)

    # ── Assemble output ────────────────────────────────────────────────────
    raw_df["if_score"]      = np.round(if_scores, 6)
    raw_df["max_zscore"]    = np.round(max_zscore, 4)
    raw_df["risk_level"]    = risk_levels
    raw_df["anomaly_params"] = [",".join(p) for p in flagged_params]

    return raw_df


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rolling_zscore(
    df: pd.DataFrame,
    cols: list[str],
    window: int,
) -> pd.DataFrame:
    """
    Compute rolling Z-scores for each column.
    Uses min_periods=10 so early rows still get a score.
    Fills any remaining NaN with 0 (perfectly normal).
    """
    result = pd.DataFrame(index=df.index)
    for col in cols:
        series = df[col].astype(float)
        roll_mean = series.rolling(window=window, min_periods=10).mean()
        roll_std  = series.rolling(window=window, min_periods=10).std()
        # Avoid division by zero on constant segments
        safe_std = roll_std.replace(0.0, np.nan)
        z = (series - roll_mean) / safe_std
        result[col] = z.fillna(0.0)
    return result


def _classify(
    if_scores: np.ndarray,
    max_zscores: np.ndarray,
) -> list[str]:
    """Apply the risk thresholds defined in the plan."""
    levels = []
    for if_s, z_s in zip(if_scores, max_zscores):
        if if_s < IF_CRITICAL or z_s > Z_CRITICAL:
            levels.append("Critical")
        elif if_s < IF_WARNING or z_s > Z_WARNING:
            levels.append("Warning")
        else:
            levels.append("Normal")
    return levels


# ---------------------------------------------------------------------------
# Anomaly summary helpers (used by the route layer)
# ---------------------------------------------------------------------------

def anomaly_rows_only(anomaly_df: pd.DataFrame) -> pd.DataFrame:
    """Return only rows classified as Warning or Critical."""
    return anomaly_df[anomaly_df["risk_level"] != "Normal"].copy()


def risk_counts(anomaly_df: pd.DataFrame) -> dict:
    """{ 'Normal': n, 'Warning': n, 'Critical': n, 'total_anomalies': n }"""
    vc = anomaly_df["risk_level"].value_counts().to_dict()
    normal   = int(vc.get("Normal", 0))
    warning  = int(vc.get("Warning", 0))
    critical = int(vc.get("Critical", 0))
    return {
        "Normal":           normal,
        "Warning":          warning,
        "Critical":         critical,
        "total_anomalies":  warning + critical,
        "total_rows":       len(anomaly_df),
    }


def param_anomaly_counts(anomaly_df: pd.DataFrame) -> dict[str, int]:
    """Count how many Warning+Critical rows flagged each parameter."""
    counts: dict[str, int] = {}
    non_normal = anomaly_df[anomaly_df["risk_level"] != "Normal"]
    for params_str in non_normal["anomaly_params"]:
        for p in params_str.split(","):
            p = p.strip()
            if p:
                counts[p] = counts.get(p, 0) + 1
    return counts
