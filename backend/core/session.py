"""
SatInsight AI — In-Memory Session Store
Holds processed DataFrames and their metadata keyed by session UUID.
Thread-safe for single-process uvicorn (the default MVP deployment).
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from core.config import settings


@dataclass
class SessionData:
    session_id: str
    dataset_name: str
    raw_df: pd.DataFrame           # original, cleaned DataFrame
    processed_df: pd.DataFrame     # normalized copy used by ML
    row_count: int
    column_names: list[str]
    created_at: float = field(default_factory=time.time)
    # Set by Sub-Task 3 after anomaly detection runs
    anomaly_df: Optional[pd.DataFrame] = None
    insights: Optional[list[dict]] = None


class SessionStore:
    """UUID-keyed, TTL-aware in-memory store for active datasets."""

    def __init__(self) -> None:
        self._store: dict[str, SessionData] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        dataset_name: str,
        raw_df: pd.DataFrame,
        processed_df: pd.DataFrame,
    ) -> SessionData:
        session_id = str(uuid.uuid4())
        data = SessionData(
            session_id=session_id,
            dataset_name=dataset_name,
            raw_df=raw_df,
            processed_df=processed_df,
            row_count=len(raw_df),
            column_names=list(raw_df.columns),
        )
        with self._lock:
            self._evict_expired()
            self._store[session_id] = data
        return data

    def update_anomalies(
        self,
        session_id: str,
        anomaly_df: pd.DataFrame,
        insights: list[dict],
    ) -> None:
        """Called by Sub-Task 3 after anomaly detection completes."""
        with self._lock:
            if session_id in self._store:
                self._store[session_id].anomaly_df = anomaly_df
                self._store[session_id].insights = insights

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            self._evict_expired()
            return self._store.get(session_id)

    def list_sessions(self) -> list[dict]:
        with self._lock:
            self._evict_expired()
            return [
                {
                    "session_id": s.session_id,
                    "dataset_name": s.dataset_name,
                    "row_count": s.row_count,
                    "columns": s.column_names,
                    "created_at": s.created_at,
                    "has_anomalies": s.anomaly_df is not None,
                }
                for s in self._store.values()
            ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _evict_expired(self) -> None:
        now = time.time()
        ttl = settings.session_ttl_seconds
        expired = [sid for sid, s in self._store.items() if now - s.created_at > ttl]
        for sid in expired:
            del self._store[sid]


# Singleton — imported and used across all routes
store = SessionStore()
