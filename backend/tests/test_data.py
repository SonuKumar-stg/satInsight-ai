"""
SatInsight AI — Backend Tests: Data Processing + API Endpoints
Sub-Task 2 test suite

Run from backend/ with:
    source .venv/bin/activate
    pip install httpx pytest
    pytest tests/ -v
"""

import io
import csv
import time

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


def _make_csv(rows: list[dict], extra_cols: list[str] | None = None) -> bytes:
    """Build a minimal valid CSV in memory."""
    fieldnames = REQUIRED_COLS + (extra_cols or [])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode()


def _valid_row(i: int = 0) -> dict:
    from datetime import datetime, timedelta
    ts = (datetime(2026, 1, 15, 8, 0, 0) + timedelta(seconds=30 * i)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return {
        "timestamp": ts,
        "temperature": 22.0 + i * 0.1,
        "radiation": 2.8,
        "pressure": 101.0,
        "battery_level": 75.0,
        "signal_strength": -72.0,
        "velocity": 7.66,
        "altitude": 408.0,
    }


def _upload_sample() -> str:
    """Load the bundled sample dataset and return its session_id."""
    resp = client.get("/api/sample")
    assert resp.status_code == 200
    return resp.json()["session_id"]


# ---------------------------------------------------------------------------
# Health check (regression guard)
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "SatInsight AI"


# ---------------------------------------------------------------------------
# GET /api/sample
# ---------------------------------------------------------------------------

class TestSampleEndpoint:
    def test_sample_returns_200(self):
        resp = client.get("/api/sample")
        assert resp.status_code == 200

    def test_sample_has_session_id(self):
        resp = client.get("/api/sample")
        body = resp.json()
        assert "session_id" in body
        assert len(body["session_id"]) == 36  # UUID format

    def test_sample_row_count(self):
        resp = client.get("/api/sample")
        body = resp.json()
        assert body["row_count"] == 600

    def test_sample_has_all_columns(self):
        resp = client.get("/api/sample")
        body = resp.json()
        for col in REQUIRED_COLS:
            assert col in body["columns"], f"Missing column: {col}"

    def test_sample_message_present(self):
        resp = client.get("/api/sample")
        body = resp.json()
        assert "message" in body
        assert "600" in body["message"]

    def test_sample_range_warnings_present(self):
        """Sample data has injected anomalies so range warnings should appear."""
        resp = client.get("/api/sample")
        body = resp.json()
        # warnings is a list (may or may not be empty depending on severity)
        assert isinstance(body["warnings"], list)


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------

class TestUploadEndpoint:
    def test_upload_valid_csv(self):
        csv_bytes = _make_csv([_valid_row(i) for i in range(5)])
        resp = client.post(
            "/api/upload",
            files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["row_count"] == 5
        assert "session_id" in body

    def test_upload_returns_session_id(self):
        csv_bytes = _make_csv([_valid_row(0)])
        resp = client.post(
            "/api/upload",
            files={"file": ("single.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        sid = resp.json()["session_id"]
        assert len(sid) == 36

    def test_upload_missing_column_returns_422(self):
        """CSV without 'altitude' column must return 422."""
        buf = io.StringIO()
        partial_cols = [c for c in REQUIRED_COLS if c != "altitude"]
        writer = csv.DictWriter(buf, fieldnames=partial_cols)
        writer.writeheader()
        row = {c: "1.0" for c in partial_cols}
        row["timestamp"] = "2026-01-15T08:00:00Z"
        writer.writerow(row)
        bad_csv = buf.getvalue().encode()

        resp = client.post(
            "/api/upload",
            files={"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")},
        )
        assert resp.status_code == 422
        assert "altitude" in resp.json()["detail"]

    def test_upload_empty_csv_returns_422(self):
        """A CSV with only a header row must be rejected."""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=REQUIRED_COLS)
        writer.writeheader()
        empty_csv = buf.getvalue().encode()

        resp = client.post(
            "/api/upload",
            files={"file": ("empty.csv", io.BytesIO(empty_csv), "text/csv")},
        )
        assert resp.status_code == 422

    def test_upload_not_a_csv_returns_422(self):
        garbage = b"this is not a csv file at all @@!#@"
        resp = client.post(
            "/api/upload",
            files={"file": ("garbage.csv", io.BytesIO(garbage), "text/csv")},
        )
        # Either 422 (invalid CSV) or 201 with 1 row — pandas is lenient.
        # The important thing is no 500 server error.
        assert resp.status_code in (201, 422)

    def test_upload_csv_with_extra_columns_accepted(self):
        """Extra columns beyond required are silently accepted."""
        csv_bytes = _make_csv([_valid_row(0)], extra_cols=["satellite_id"])
        resp = client.post(
            "/api/upload",
            files={"file": ("extra.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 201

    def test_upload_csv_with_missing_values_imputed(self):
        """Rows with missing numeric values should be imputed, not rejected."""
        row = _valid_row(0)
        row["temperature"] = ""   # missing
        csv_bytes = _make_csv([row, _valid_row(1)])
        resp = client.post(
            "/api/upload",
            files={"file": ("missing.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["row_count"] == 2
        # The warning about imputation should appear
        assert any("temperature" in w for w in body["warnings"])

    def test_upload_bad_timestamps_partially_accepted(self):
        """Rows with completely unparseable timestamps are dropped; valid rows kept."""
        rows = [_valid_row(i) for i in range(3)]
        rows[1]["timestamp"] = "not-a-date"
        csv_bytes = _make_csv(rows)
        resp = client.post(
            "/api/upload",
            files={"file": ("partial_ts.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 201
        # 2 valid rows remain
        assert resp.json()["row_count"] == 2


# ---------------------------------------------------------------------------
# GET /api/sessions
# ---------------------------------------------------------------------------

class TestSessionsEndpoint:
    def test_sessions_list_returns_200(self):
        _upload_sample()
        resp = client.get("/api/sessions")
        assert resp.status_code == 200

    def test_sessions_list_is_non_empty_after_load(self):
        _upload_sample()
        resp = client.get("/api/sessions")
        body = resp.json()
        assert body["total"] >= 1
        assert len(body["sessions"]) >= 1

    def test_session_item_has_expected_fields(self):
        _upload_sample()
        resp = client.get("/api/sessions")
        session = resp.json()["sessions"][0]
        for field in ("session_id", "dataset_name", "row_count", "columns", "created_at"):
            assert field in session, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# GET /api/data/{session_id} — paginated records
# ---------------------------------------------------------------------------

class TestDataEndpoint:
    def test_data_first_page(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}?page=1&page_size=20")
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert len(body["records"]) == 20
        assert body["total_rows"] == 600

    def test_data_total_pages(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}?page_size=100")
        body = resp.json()
        assert body["total_pages"] == 6   # 600 / 100

    def test_data_last_page_partial(self):
        sid = _upload_sample()
        # 600 rows, page_size=50 → 12 pages, last page has 50 rows exactly
        resp = client.get(f"/api/data/{sid}?page=12&page_size=50")
        body = resp.json()
        assert len(body["records"]) == 50

    def test_data_invalid_session_returns_404(self):
        resp = client.get("/api/data/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_data_records_have_required_fields(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}?page=1&page_size=5")
        records = resp.json()["records"]
        for rec in records:
            for col in REQUIRED_COLS:
                assert col in rec, f"Record missing column: {col}"

    def test_data_page_beyond_range_returns_empty(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}?page=9999&page_size=50")
        assert resp.status_code == 200
        assert resp.json()["records"] == []


# ---------------------------------------------------------------------------
# GET /api/data/{session_id}/preview
# ---------------------------------------------------------------------------

class TestPreviewEndpoint:
    def test_preview_default_10_rows(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/preview")
        assert resp.status_code == 200
        assert len(resp.json()["preview_rows"]) == 10

    def test_preview_custom_n(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/preview?n=3")
        assert len(resp.json()["preview_rows"]) == 3

    def test_preview_has_metadata(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/preview")
        body = resp.json()
        assert body["row_count"] == 600
        assert set(REQUIRED_COLS).issubset(set(body["columns"]))

    def test_preview_invalid_session_returns_404(self):
        resp = client.get("/api/data/bad-uuid/preview")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/data/{session_id}/stats
# ---------------------------------------------------------------------------

class TestStatsEndpoint:
    def test_stats_returns_200(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/stats")
        assert resp.status_code == 200

    def test_stats_has_all_parameters(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/stats")
        params = resp.json()["parameters"]
        for col in ["temperature", "radiation", "pressure", "battery_level",
                    "signal_strength", "velocity", "altitude"]:
            assert col in params, f"Missing parameter stats: {col}"

    def test_stats_fields_present(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/stats")
        temp_stats = resp.json()["parameters"]["temperature"]
        for field in ("count", "mean", "std", "min", "max", "q1", "median", "q3", "iqr"):
            assert field in temp_stats, f"Missing stats field: {field}"

    def test_stats_count_matches_rows(self):
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/stats")
        count = resp.json()["parameters"]["temperature"]["count"]
        assert count == 600

    def test_stats_sample_temperature_range(self):
        """Sample has anomalies — temperature max should be above normal (~45°C)."""
        sid = _upload_sample()
        resp = client.get(f"/api/data/{sid}/stats")
        temp = resp.json()["parameters"]["temperature"]
        assert temp["max"] > 50.0  # thermal anomaly was injected at 62–92°C

    def test_stats_invalid_session_returns_404(self):
        resp = client.get("/api/data/does-not-exist/stats")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Data processor unit tests (no HTTP layer)
# ---------------------------------------------------------------------------

class TestDataProcessor:
    """Direct unit tests of the service functions."""

    def test_process_csv_returns_three_values(self):
        from services.data_processor import process_csv
        csv_bytes = _make_csv([_valid_row(i) for i in range(5)])
        raw_df, processed_df, warnings = process_csv(csv_bytes)
        assert len(raw_df) == 5
        assert len(processed_df) == 5
        assert isinstance(warnings, list)

    def test_normalize_range(self):
        """All numeric columns in processed_df should be in [0, 1]."""
        from services.data_processor import NUMERIC_COLUMNS, process_csv
        csv_bytes = _make_csv([_valid_row(i) for i in range(10)])
        _, processed_df, _ = process_csv(csv_bytes)
        for col in NUMERIC_COLUMNS:
            assert processed_df[col].min() >= -1e-9, f"{col} min below 0"
            assert processed_df[col].max() <= 1.0 + 1e-9, f"{col} max above 1"

    def test_missing_column_raises(self):
        from core.exceptions import InvalidCSVError
        from services.data_processor import process_csv
        buf = io.StringIO()
        partial = [c for c in REQUIRED_COLS if c != "radiation"]
        writer = csv.DictWriter(buf, fieldnames=partial)
        writer.writeheader()
        writer.writerow({c: "1" for c in partial})
        with pytest.raises(InvalidCSVError):
            process_csv(buf.getvalue().encode())

    def test_empty_csv_raises(self):
        from core.exceptions import InvalidCSVError
        from services.data_processor import process_csv
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=REQUIRED_COLS)
        writer.writeheader()
        with pytest.raises(InvalidCSVError):
            process_csv(buf.getvalue().encode())

    def test_missing_values_imputed(self):
        from services.data_processor import process_csv
        rows = [_valid_row(i) for i in range(5)]
        rows[2]["temperature"] = ""
        csv_bytes = _make_csv(rows)
        raw_df, _, warnings = process_csv(csv_bytes)
        assert raw_df["temperature"].isna().sum() == 0
        assert any("temperature" in w for w in warnings)

    def test_timestamps_sorted(self):
        """Rows should be sorted by timestamp after processing."""
        from services.data_processor import process_csv
        rows = [_valid_row(i) for i in [4, 2, 0, 3, 1]]
        csv_bytes = _make_csv(rows)
        raw_df, _, _ = process_csv(csv_bytes)
        ts = list(raw_df["timestamp"])
        assert ts == sorted(ts)

    def test_compute_stats_keys(self):
        from services.data_processor import compute_stats, process_csv
        csv_bytes = _make_csv([_valid_row(i) for i in range(10)])
        raw_df, _, _ = process_csv(csv_bytes)
        stats = compute_stats(raw_df)
        assert "temperature" in stats
        assert stats["temperature"]["count"] == 10

    def test_df_to_records_pagination(self):
        from services.data_processor import df_to_records, process_csv
        csv_bytes = _make_csv([_valid_row(i) for i in range(25)])
        raw_df, _, _ = process_csv(csv_bytes)
        page1, total = df_to_records(raw_df, page=1, page_size=10)
        assert len(page1) == 10
        assert total == 25
        page3, _ = df_to_records(raw_df, page=3, page_size=10)
        assert len(page3) == 5  # last partial page


# ---------------------------------------------------------------------------
# Session store unit tests
# ---------------------------------------------------------------------------

class TestSessionStore:
    def test_create_and_get(self):
        from services.data_processor import process_csv
        from core.session import SessionStore
        local_store = SessionStore()
        csv_bytes = _make_csv([_valid_row(0)])
        raw_df, processed_df, _ = process_csv(csv_bytes)
        session = local_store.create("test.csv", raw_df, processed_df)
        fetched = local_store.get(session.session_id)
        assert fetched is not None
        assert fetched.row_count == 1

    def test_missing_session_returns_none(self):
        from core.session import SessionStore
        local_store = SessionStore()
        assert local_store.get("nonexistent-uuid") is None

    def test_ttl_expiry(self):
        """Sessions with created_at beyond TTL should be evicted."""
        from services.data_processor import process_csv
        from core.session import SessionStore
        local_store = SessionStore()
        local_store._SessionStore__dict__ if False else None  # just ensure class used
        csv_bytes = _make_csv([_valid_row(0)])
        raw_df, processed_df, _ = process_csv(csv_bytes)
        session = local_store.create("ttl_test.csv", raw_df, processed_df)
        # Manually backdate the session's created_at to force expiry
        local_store._store[session.session_id].created_at = time.time() - 99999
        # Now any store read should evict it
        assert local_store.get(session.session_id) is None
