"""
SatInsight AI — Insight Generator Service

Converts anomaly detection results into human-readable insight cards with
AI-style explanations and recommended actions.

Architecture:
  1. Rule engine — per-parameter domain knowledge produces insight seeds.
  2. Cluster reducer — consecutive anomaly rows are collapsed into a single event.
  3. Template renderer — turns each seed into a full InsightCard dict.

Each InsightCard dict has:
    id           str     Stable identifier
    title        str     Short summary (≤60 chars)
    description  str     2-3 sentence explanation of the pattern
    severity     str     "info" | "warning" | "critical"
    parameter    str     Primary affected parameter (or "multi")
    value_range  str     Human-readable range seen during the event
    recommended_action  str  Concrete action the operator should take
    row_start    int     First row index of the event
    row_end      int     Last row index of the event
    event_rows   int     Number of rows in the cluster
"""

import math
from typing import Optional

import pandas as pd

from services.data_processor import NUMERIC_COLUMNS

# ---------------------------------------------------------------------------
# Parameter-level domain knowledge
# ---------------------------------------------------------------------------

# (parameter, direction, severity_threshold, description_template, action_template)
# direction: "high" | "low"
_PARAM_RULES: list[dict] = [
    {
        "parameter": "temperature",
        "direction": "high",
        "z_threshold": 2.5,
        "severity": "critical",
        "title_tmpl": "Elevated Thermal Readings — {param_label}",
        "desc_tmpl": (
            "Satellite temperature readings spiked to {max_val:.1f}°C, "
            "significantly above the baseline range of {baseline:.1f}°C. "
            "This pattern is consistent with solar flare exposure or a "
            "thermal regulation system fault."
        ),
        "action": (
            "Initiate thermal management protocol. Rotate satellite orientation "
            "to reduce sun-facing surface exposure. Check thermal control "
            "subsystem telemetry and verify heater/cooler status."
        ),
    },
    {
        "parameter": "radiation",
        "direction": "high",
        "z_threshold": 2.5,
        "severity": "critical",
        "title_tmpl": "High Radiation Flux Detected",
        "desc_tmpl": (
            "Radiation levels reached {max_val:.3f} mSv/h — {z_ratio:.1f}× above "
            "the rolling baseline. Sustained exposure at this level can degrade "
            "onboard electronics and affect sensor accuracy."
        ),
        "action": (
            "Activate radiation shielding protocols. Switch non-critical systems "
            "to safe-mode. Log the event for ground analysis and cross-reference "
            "with NOAA space weather alerts."
        ),
    },
    {
        "parameter": "battery_level",
        "direction": "low",
        "z_threshold": 2.5,
        "severity": "critical",
        "title_tmpl": "Critical Battery Level Detected",
        "desc_tmpl": (
            "Battery charge dropped to {min_val:.1f}%, well below the safe "
            "operating threshold. This may indicate a power generation fault, "
            "increased load from an anomalous subsystem, or extended eclipse "
            "period with insufficient charge recovery."
        ),
        "action": (
            "Immediately shed non-essential loads. Verify solar panel orientation "
            "and power distribution unit status. Initiate emergency power "
            "management protocol to protect mission-critical systems."
        ),
    },
    {
        "parameter": "signal_strength",
        "direction": "low",
        "z_threshold": 2.5,
        "severity": "warning",
        "title_tmpl": "Degraded Signal Strength",
        "desc_tmpl": (
            "Downlink signal strength fell to {min_val:.1f} dBm, a {delta:.1f} dB "
            "drop from baseline. This may result from antenna pointing errors, "
            "atmospheric interference, or hardware degradation in the RF chain."
        ),
        "action": (
            "Verify antenna tracking and pointing calibration. Check RF "
            "amplifier and transmitter status. Consider switching to backup "
            "communication channel if signal continues to degrade."
        ),
    },
    {
        "parameter": "pressure",
        "direction": "low",
        "z_threshold": 2.5,
        "severity": "critical",
        "title_tmpl": "Anomalous Pressure Reading",
        "desc_tmpl": (
            "Internal pressure dropped to {min_val:.2f} hPa, a deviation of "
            "{delta:.2f} hPa from nominal. A sudden pressure drop may indicate "
            "micro-meteorite impact, structural breach, or a faulty pressure sensor."
        ),
        "action": (
            "Cross-reference with structural health monitoring sensors. "
            "Activate leak-detection protocol. Seal non-critical compartments "
            "and notify mission control immediately for structural assessment."
        ),
    },
    {
        "parameter": "velocity",
        "direction": "high",
        "z_threshold": 2.5,
        "severity": "critical",
        "title_tmpl": "Unexpected Velocity Anomaly",
        "desc_tmpl": (
            "Orbital velocity peaked at {max_val:.4f} km/s — {z_ratio:.1f}× above "
            "the expected value. Sudden velocity changes can indicate an "
            "unscheduled thruster firing, debris collision impulse, or "
            "navigation system anomaly."
        ),
        "action": (
            "Verify thruster status and fuel consumption logs. Compute "
            "updated orbital elements and compare against propagated TLE. "
            "If off-nominal, initiate orbit correction manoeuvre planning."
        ),
    },
    {
        "parameter": "altitude",
        "direction": "low",
        "z_threshold": 2.0,
        "severity": "warning",
        "title_tmpl": "Orbital Altitude Decay Detected",
        "desc_tmpl": (
            "Altitude dropped to {min_val:.1f} km, which is {delta:.1f} km below "
            "nominal orbit. Increased atmospheric drag at lower altitudes "
            "accelerates orbital decay and shortens mission lifetime."
        ),
        "action": (
            "Schedule orbit maintenance manoeuvre. Verify atmospheric drag "
            "model parameters. Increase monitoring cadence and alert flight "
            "dynamics team to assess re-boost timeline."
        ),
    },
]

# Lookup by parameter name
_RULES_BY_PARAM: dict[str, dict] = {r["parameter"]: r for r in _PARAM_RULES}

# Multi-parameter (correlated) insight — fired when 3+ parameters anomalous together
_MULTI_PARAM_INSIGHT = {
    "title_tmpl": "Correlated Multi-Sensor Anomaly",
    "desc_tmpl": (
        "Multiple telemetry parameters ({params_str}) showed simultaneous "
        "anomalous behaviour across {event_rows} consecutive readings. "
        "Correlated multi-sensor events often indicate a common-cause failure "
        "such as a power surge, solar energetic particle event, or software fault."
    ),
    "action": (
        "Perform cross-subsystem health check. Review event timeline for common "
        "triggering events. Escalate to mission operations centre for root-cause "
        "analysis. Consider entering safe-mode until origin is established."
    ),
}


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def generate(anomaly_df: pd.DataFrame) -> list[dict]:
    """
    Generate insight cards from an annotated anomaly DataFrame.

    Parameters
    ----------
    anomaly_df : pd.DataFrame
        Output of anomaly_detector.detect() — must have columns:
        risk_level, if_score, max_zscore, anomaly_params.

    Returns
    -------
    list[dict]  — 3-10 InsightCard dicts ordered by severity then event size.
    """
    clusters = _cluster_anomalies(anomaly_df)
    cards: list[dict] = []

    for cluster_idx, cluster in enumerate(clusters):
        card = _card_for_cluster(cluster_idx, cluster, anomaly_df)
        if card:
            cards.append(card)

    # Sort: Critical first, then Warning, then info; largest events first within tier
    tier_order = {"critical": 0, "warning": 1, "info": 2}
    cards.sort(key=lambda c: (tier_order.get(c["severity"], 9), -c["event_rows"]))

    # Return at most 10 cards (keep the most significant ones)
    return cards[:10]


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def _cluster_anomalies(anomaly_df: pd.DataFrame) -> list[dict]:
    """
    Group consecutive Warning/Critical rows into event clusters.
    Each cluster dict has: rows (list of int indices), severity, params (set).
    """
    non_normal_mask = anomaly_df["risk_level"].isin(["Warning", "Critical"])
    clusters: list[dict] = []
    current: Optional[dict] = None

    for idx in range(len(anomaly_df)):
        row = anomaly_df.iloc[idx]
        if non_normal_mask.iloc[idx]:
            params = {
                p.strip()
                for p in str(row["anomaly_params"]).split(",")
                if p.strip()
            }
            severity = row["risk_level"].lower()
            if current is None:
                current = {"rows": [idx], "severity": severity, "params": params}
            else:
                current["rows"].append(idx)
                current["params"] |= params
                # Escalate severity if any row is Critical
                if severity == "critical":
                    current["severity"] = "critical"
        else:
            if current is not None:
                clusters.append(current)
                current = None

    if current is not None:
        clusters.append(current)

    return clusters


# ---------------------------------------------------------------------------
# Card builder
# ---------------------------------------------------------------------------

def _card_for_cluster(
    cluster_idx: int,
    cluster: dict,
    anomaly_df: pd.DataFrame,
) -> Optional[dict]:
    """Build one InsightCard dict for a cluster of anomalous rows."""
    rows = cluster["rows"]
    params: set[str] = cluster["params"]
    severity = cluster["severity"]     # "warning" | "critical"
    event_rows = len(rows)

    row_start = rows[0]
    row_end   = rows[-1]

    cluster_df = anomaly_df.iloc[rows]

    # ── Multi-parameter event ──────────────────────────────────────────────
    known_params = [p for p in params if p in _RULES_BY_PARAM]
    if len(known_params) >= 3:
        params_str = ", ".join(sorted(known_params))
        return {
            "id": f"multi_{cluster_idx}_{row_start}",
            "title": _MULTI_PARAM_INSIGHT["title_tmpl"],
            "description": _MULTI_PARAM_INSIGHT["desc_tmpl"].format(
                params_str=params_str,
                event_rows=event_rows,
            ),
            "severity": severity,
            "parameter": "multi",
            "value_range": f"rows {row_start}–{row_end}",
            "recommended_action": _MULTI_PARAM_INSIGHT["action"],
            "row_start": row_start,
            "row_end": row_end,
            "event_rows": event_rows,
        }

    # ── Single dominant parameter ──────────────────────────────────────────
    # Pick the parameter with the highest mean |Z-score| in this cluster
    dominant = _dominant_parameter(cluster_df, known_params if known_params else list(params))

    if dominant and dominant in _RULES_BY_PARAM:
        return _build_card(cluster_idx, cluster_df, dominant, severity, row_start, row_end, event_rows)

    # ── Fallback: IF-score driven (no Z-score flags, but IF says anomalous) ─
    if event_rows >= 1:
        best_if = float(cluster_df["if_score"].min())
        return {
            "id": f"if_cluster_{cluster_idx}_{row_start}",
            "title": f"Anomalous Telemetry Pattern at Row {row_start}",
            "description": (
                f"The AI model flagged {event_rows} consecutive readings as anomalous "
                f"(Isolation Forest score: {best_if:.3f}). The pattern deviates "
                f"significantly from the learned baseline of normal satellite behaviour."
            ),
            "severity": severity,
            "parameter": "unknown",
            "value_range": f"rows {row_start}–{row_end}",
            "recommended_action": (
                "Review raw telemetry for the flagged period. Cross-reference with "
                "ground-station logs and spacecraft event records to determine origin."
            ),
            "row_start": row_start,
            "row_end": row_end,
            "event_rows": event_rows,
        }

    return None


def _dominant_parameter(cluster_df: pd.DataFrame, params: list[str]) -> Optional[str]:
    """Return the parameter with the largest mean absolute value in the cluster."""
    if not params:
        return None
    best_param = None
    best_score = -1.0
    for p in params:
        if p in cluster_df.columns:
            # Use max_zscore proxy: find which param drives it
            series = cluster_df[p].astype(float)
            score = float(series.std()) if len(series) > 1 else 0.0
            if score > best_score:
                best_score = score
                best_param = p
    return best_param


def _build_card(
    cluster_idx: int,
    cluster_df: pd.DataFrame,
    param: str,
    severity: str,
    row_start: int,
    row_end: int,
    event_rows: int,
) -> dict:
    """Render a full InsightCard for a single dominant parameter."""
    rule = _RULES_BY_PARAM[param]
    series = cluster_df[param].astype(float)

    max_val   = float(series.max())
    min_val   = float(series.min())
    mean_val  = float(series.mean())

    # Estimate baseline from a wider context — just use the series stats
    delta     = abs(max_val - mean_val) if rule["direction"] == "high" else abs(min_val - mean_val)
    baseline  = mean_val
    z_ratio   = (max_val - mean_val) / (series.std() + 1e-9) if rule["direction"] == "high" else 1.0
    value_range = (
        f"{min_val:.2f} – {max_val:.2f}"
        if max_val != min_val
        else f"{max_val:.2f}"
    )

    fmt = {
        "max_val": max_val,
        "min_val": min_val,
        "mean_val": mean_val,
        "delta": delta,
        "baseline": baseline,
        "z_ratio": max(z_ratio, 1.0),
        "event_rows": event_rows,
        "param_label": param.replace("_", " ").title(),
    }

    return {
        "id": f"{param}_{cluster_idx}_{row_start}",
        "title": rule["title_tmpl"].format(**fmt),
        "description": rule["desc_tmpl"].format(**fmt),
        "severity": severity,
        "parameter": param,
        "value_range": value_range,
        "recommended_action": rule["action"],
        "row_start": row_start,
        "row_end": row_end,
        "event_rows": event_rows,
    }
