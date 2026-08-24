"""
SatInsight AI — Custom HTTP Exceptions
"""

from fastapi import HTTPException


class SessionNotFoundError(HTTPException):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=404,
            detail=f"Session '{session_id}' not found or has expired. Load or upload a dataset first.",
        )


class NoDataLoadedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="No dataset loaded. Call GET /api/sample or POST /api/upload first.",
        )


class InvalidCSVError(HTTPException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=422,
            detail=f"Invalid CSV file: {reason}",
        )


class FileTooLargeError(HTTPException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=413,
            detail=f"Uploaded file exceeds the {max_mb} MB limit.",
        )
