"""
SatInsight AI — Backend Tests: Anomaly Detection + AI Insights
Sub-Task 3 test suite

Run from backend/ with:
    source .venv/bin/activate
    pytest tests/test_anomalies.py -v
"""

import io
import csv
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_COLS = [
    "timestamp", "temperature", "radiation", "pressure",
    "battery_level", "signal_strength", "velocity", "altitude",
]


def _ts(i: int) -> str:
    return (datetime(2026, 1, 15, 8, 0, 0) + timedelta(seconds=30 * i)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _make_csv_with_anomalies() -> bytes:
    """
    200-row CSV with explicit anomaly spikes that the detector must catch.
    Rows 50-55: temperature spike (80°C instead of normal ~22°C)
    Rows 100-103: battery drain (5%)
    Row 150: isolated radiation spike (12 mSv/h)
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=REQUIRED_COLS)
    writer.writeheader()
    for i in range(200):
        temp = 22.0 + 0.5 * (i % 10)
        rad  = 2.8
        bat  = 75.0
        sig  = -72.0
        vel  = 7.66
        pres = 101.0
        alt  = 408.0

        if 50 <= i <= 55:
            temp = 80.0 + i * 0.2   # thermal anomaly
        if 100 <= i <= 103:
            bat = 5.0 + i * 0.1     # battery drain
        if i == 150:
            rad = 12.0              # radiation spike

        writer.writerow({
            "timestamp":      _ts(i),
            "temperature":    temp,
            "radiation":      rad,
            "pressure":       pres,
            "battery_level":  bat,
            "signal_strength": sig,
            "velocity":       vel,
            "altitude":       alt,
        })
    return buf.getvalue().encode()


def _load_sample() -> str:
    """Load the bundled sample dataset, return session_id."""
    resp = client.get("/api/sample")
    assert resp.status_code == 200
    return resp.json()["session_id"]


def _load_custom() -> str:
    """Upload the custom anomaly CSV, return session_id."""
    csv_bytes = _make_csv_with_anomalies()
    resp = client.post(
        "/api/upload",
        files={"file": ("anomaly_test.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 201
    return resp.json()["session_id"]


def _analyze(session_id: str) -> dict:
    resp = client.post(f"/api/analyze/{session_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Anomaly Detector — unit tests (no HTTP)
# ---------------------------------------------------------------------------

class TestAnomalyDetectorUnit:
    def test_detect_returns_dataframe_with_new_columns(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        assert "if_score" in result.columns
        assert "max_zscore" in result.columns
        assert "risk_level" in result.columns
        assert "anomaly_params" in result.columns

    def test_detect_row_count_preserved(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        assert len(result) == 200

    def test_detect_risk_levels_valid(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        assert set(result["risk_level"].unique()).issubset({"Normal", "Warning", "Critical"})

    def test_detect_finds_anomalies_in_injected_data(self):
        """The injected spikes must produce at least some Warning/Critical rows."""
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        n_anomalies = (result["risk_level"] != "Normal").sum()
        assert n_anomalies >= 5, f"Expected ≥5 anomalies, got {n_anomalies}"

    def test_if_score_range(self):
        """Isolation Forest decision_function scores must be finite floats."""
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect
        import math

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        for score in result["if_score"]:
            assert math.isfinite(float(score)), f"Non-finite IF score: {score}"

    def test_risk_counts_helper(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect, risk_counts

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        counts = risk_counts(result)
        assert counts["total_rows"] == 200
        assert counts["Normal"] + counts["Warning"] + counts["Critical"] == 200
        assert counts["total_anomalies"] == counts["Warning"] + counts["Critical"]

    def test_sample_dataset_produces_many_anomalies(self):
        """The 600-row sample dataset should flag at least 20 Warning+Critical rows."""
        from services.data_processor import process_csv, NUMERIC_COLUMNS
        from core.session import SessionStore
        from services.anomaly_detector import detect, risk_counts
        from pathlib import Path

        sample_path = Path(__file__).parent.parent / "data" / "sample_satellite.csv"
        raw_df, processed_df, _ = process_csv(sample_path)
        local_store = SessionStore()
        session = local_store.create("sample.csv", raw_df, processed_df)

        result = detect(session)
        counts = risk_counts(result)
        assert counts["total_anomalies"] >= 20, (
            f"Expected ≥20 anomalies from sample data, got {counts['total_anomalies']}"
        )

    def test_anomaly_rows_only_filters_correctly(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect, anomaly_rows_only

        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)

        result = detect(session)
        anomalies = anomaly_rows_only(result)
        # All returned rows must be non-Normal
        assert all(anomalies["risk_level"] != "Normal")


# ---------------------------------------------------------------------------
# Insight Generator — unit tests (no HTTP)
# ---------------------------------------------------------------------------

class TestInsightGeneratorUnit:
    def _get_anomaly_df(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect
        csv_bytes = _make_csv_with_anomalies()
        raw_df, processed_df, _ = process_csv(csv_bytes)
        local_store = SessionStore()
        session = local_store.create("test.csv", raw_df, processed_df)
        return detect(session)

    def test_generate_returns_list(self):
        from services.insight_generator import generate
        anomaly_df = self._get_anomaly_df()
        insights = generate(anomaly_df)
        assert isinstance(insights, list)

    def test_generate_at_least_one_insight(self):
        """Injected anomalies must produce at least 1 insight card."""
        from services.insight_generator import generate
        anomaly_df = self._get_anomaly_df()
        insights = generate(anomaly_df)
        assert len(insights) >= 1, "Expected at least 1 insight card"

    def test_generate_at_most_ten_insights(self):
        from services.insight_generator import generate
        anomaly_df = self._get_anomaly_df()
        insights = generate(anomaly_df)
        assert len(insights) <= 10

    def test_insight_card_has_required_fields(self):
        from services.insight_generator import generate
        anomaly_df = self._get_anomaly_df()
        insights = generate(anomaly_df)
        required = {
            "id", "title", "description", "severity",
            "parameter", "value_range", "recommended_action",
            "row_start", "row_end", "event_rows",
        }
        for card in insights:
            missing = required - set(card.keys())
            assert not missing, f"Card missing fields: {missing}"

    def test_insight_severity_values(self):
        from services.insight_generator import generate
        anomaly_df = self._get_anomaly_df()
        insights = generate(anomaly_df)
        for card in insights:
            assert card["severity"] in ("info", "warning", "critical"), (
                f"Unexpected severity: {card['severity']}"
            )

    def test_sample_produces_multiple_insights(self):
        """Sample dataset should yield 3-10 insight cards."""
        from services.data_processor import process_csv
        from core.session import SessionStore
        from services.anomaly_detector import detect
        from services.insight_generator import generate
        from pathlib import Path

        sample_path = Path(__file__).parent.parent / "data" / "sample_satellite.csv"
        raw_df, processed_df, _ = process_csv(sample_path)
        local_store = SessionStore()
        session = local_store.create("sample.csv", raw_df, processed_df)
        anomaly_df = detect(session)
        insights = generate(anomaly_df)
        assert len(insights) >= 3, f"Expected ≥3 insights, got {len(insights)}"
        assert len(insights) <= 10


# ---------------------------------------------------------------------------
# POST /api/analyze/{session_id}
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    def test_analyze_returns_200(self):
        sid = _load_sample()
        resp = client.post(f"/api/analyze/{sid}")
        assert resp.status_code == 200

    def test_analyze_response_has_required_fields(self):
        sid = _load_sample()
        body = _analyze(sid)
        for field in ("session_id", "dataset_name", "row_count", "risk_counts",
                      "param_anomaly_counts", "message"):
            assert field in body, f"Missing field: {field}"

    def test_analyze_risk_counts_sum_to_total(self):
        sid = _load_sample()
        body = _analyze(sid)
        rc = body["risk_counts"]
        assert rc["Normal"] + rc["Warning"] + rc["Critical"] == rc["total_rows"]

    def test_analyze_total_rows_matches_dataset(self):
        sid = _load_sample()
        body = _analyze(sid)
        assert body["risk_counts"]["total_rows"] == 600

    def test_analyze_sample_produces_anomalies(self):
        """The sample dataset has injected anomalies — must find at least 20."""
        sid = _load_sample()
        body = _analyze(sid)
        total = body["risk_counts"]["total_anomalies"]
        assert total >= 20, f"Expected ≥20 anomalies, got {total}"

    def test_analyze_critical_anomalies_present(self):
        """Sample data has Critical-level injections — must detect at least 5."""
        sid = _load_sample()
        body = _analyze(sid)
        assert body["risk_counts"]["Critical"] >= 5

    def test_analyze_invalid_session_returns_404(self):
        resp = client.post("/api/analyze/does-not-exist")
        assert resp.status_code == 404

    def test_analyze_custom_csv_with_anomalies(self):
        sid = _load_custom()
        body = _analyze(sid)
        # Our custom CSV has clear spikes — must detect them
        assert body["risk_counts"]["total_anomalies"] >= 5

    def test_analyze_param_anomaly_counts_non_empty(self):
        sid = _load_sample()
        body = _analyze(sid)
        assert len(body["param_anomaly_counts"]) >= 1

    def test_analyze_message_contains_counts(self):
        sid = _load_sample()
        body = _analyze(sid)
        assert "anomalies detected" in body["message"].lower() or "analysis complete" in body["message"].lower()


# ---------------------------------------------------------------------------
# GET /api/anomalies/{session_id}
# ---------------------------------------------------------------------------

class TestAnomaliesEndpoint:
    def _setup(self):
        sid = _load_sample()
        _analyze(sid)
        return sid

    def test_anomalies_returns_200(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}")
        assert resp.status_code == 200

    def test_anomalies_before_analyze_returns_400(self):
        sid = _load_sample()   # don't call analyze
        resp = client.get(f"/api/anomalies/{sid}")
        assert resp.status_code == 400

    def test_anomalies_invalid_session_returns_404(self):
        resp = client.get("/api/anomalies/no-such-session")
        assert resp.status_code == 404

    def test_anomalies_all_rows_non_normal(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}?page_size=500")
        rows = resp.json()["anomalies"]
        for row in rows:
            assert row["risk_level"] in ("Warning", "Critical"), (
                f"Unexpected risk_level in anomaly list: {row['risk_level']}"
            )

    def test_anomalies_pagination_works(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}?page=1&page_size=5")
        body = resp.json()
        assert len(body["anomalies"]) <= 5
        assert body["page"] == 1

    def test_anomalies_risk_filter_critical(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}?risk=Critical&page_size=500")
        rows = resp.json()["anomalies"]
        for row in rows:
            assert row["risk_level"] == "Critical"

    def test_anomalies_risk_filter_warning(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}?risk=Warning&page_size=500")
        rows = resp.json()["anomalies"]
        for row in rows:
            assert row["risk_level"] == "Warning"

    def test_anomalies_record_has_expected_fields(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}?page_size=1")
        row = resp.json()["anomalies"][0]
        for field in ("timestamp", "temperature", "risk_level", "if_score",
                      "max_zscore", "anomaly_params"):
            assert field in row, f"Anomaly row missing: {field}"

    def test_anomalies_anomaly_params_is_list(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}?page_size=10")
        for row in resp.json()["anomalies"]:
            assert isinstance(row["anomaly_params"], list)


# ---------------------------------------------------------------------------
# GET /api/anomalies/{session_id}/summary
# ---------------------------------------------------------------------------

class TestAnomalySummaryEndpoint:
    def _setup(self):
        sid = _load_sample()
        _analyze(sid)
        return sid

    def test_summary_returns_200(self):
        sid = self._setup()
        resp = client.get(f"/api/anomalies/{sid}/summary")
        assert resp.status_code == 200

    def test_summary_has_risk_counts(self):
        sid = self._setup()
        body = client.get(f"/api/anomalies/{sid}/summary").json()
        rc = body["risk_counts"]
        for key in ("Normal", "Warning", "Critical", "total_anomalies", "total_rows"):
            assert key in rc

    def test_summary_has_param_counts(self):
        sid = self._setup()
        body = client.get(f"/api/anomalies/{sid}/summary").json()
        assert isinstance(body["param_anomaly_counts"], dict)


# ---------------------------------------------------------------------------
# GET /api/insights/{session_id}
# ---------------------------------------------------------------------------

class TestInsightsEndpoint:
    def _setup(self):
        sid = _load_sample()
        _analyze(sid)
        return sid

    def test_insights_returns_200(self):
        sid = self._setup()
        resp = client.get(f"/api/insights/{sid}")
        assert resp.status_code == 200

    def test_insights_before_analyze_returns_400(self):
        sid = _load_sample()   # no analyze
        resp = client.get(f"/api/insights/{sid}")
        assert resp.status_code == 400

    def test_insights_invalid_session_returns_404(self):
        resp = client.get("/api/insights/fake-id")
        assert resp.status_code == 404

    def test_insights_has_at_least_3_cards(self):
        sid = self._setup()
        body = client.get(f"/api/insights/{sid}").json()
        assert body["total_insights"] >= 3, f"Expected ≥3 cards, got {body['total_insights']}"

    def test_insights_at_most_10_cards(self):
        sid = self._setup()
        body = client.get(f"/api/insights/{sid}").json()
        assert body["total_insights"] <= 10

    def test_insight_card_fields(self):
        sid = self._setup()
        body = client.get(f"/api/insights/{sid}").json()
        for card in body["insights"]:
            for field in ("id", "title", "description", "severity", "parameter",
                          "value_range", "recommended_action", "row_start",
                          "row_end", "event_rows"):
                assert field in card, f"Card missing field: {field}"

    def test_insight_severity_valid(self):
        sid = self._setup()
        body = client.get(f"/api/insights/{sid}").json()
        for card in body["insights"]:
            assert card["severity"] in ("info", "warning", "critical")

    def test_insight_recommended_action_non_empty(self):
        sid = self._setup()
        body = client.get(f"/api/insights/{sid}").json()
        for card in body["insights"]:
            assert len(card["recommended_action"]) > 20, (
                f"Recommended action too short: {card['recommended_action']}"
            )

    def test_analysis_run_flag_is_true(self):
        sid = self._setup()
        body = client.get(f"/api/insights/{sid}").json()
        assert body["analysis_run"] is True

    def test_insight_status_endpoint(self):
        sid = _load_sample()
        # Before analysis
        resp = client.get(f"/api/insights/{sid}/status")
        assert resp.status_code == 200
        assert resp.json()["analysis_run"] is False
        # After analysis
        _analyze(sid)
        resp = client.get(f"/api/insights/{sid}/status")
        assert resp.json()["analysis_run"] is True
        assert resp.json()["insight_count"] >= 1
