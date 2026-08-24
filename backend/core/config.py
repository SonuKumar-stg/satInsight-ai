"""
SatInsight AI — Backend Configuration
Reads from environment variables / .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    anomaly_contamination: float = 0.05
    session_ttl_seconds: int = 3600
    max_upload_rows: int = 100_000
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
