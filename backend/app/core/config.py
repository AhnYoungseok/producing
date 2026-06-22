from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hit Song Lab API"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/hit_song_lab.db"
    storage_dir: str = "./storage"
    export_dir: str = "./exports/hit_song_library"
    frontend_origin: str = "http://localhost:3100"
    max_upload_mb: int = 50
    audio_sample_rate: int = 22050
    auto_reference_batch_enabled: bool = True
    auto_reference_batch_interval_seconds: int = 600
    auto_reference_batch_size: int = 10
    auto_reference_batch_run_on_startup: bool = True
    lastfm_api_key: str | None = None
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @cached_property
    def database_path(self) -> Path:
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite:/// DATABASE_URL values are supported in the MVP.")
        return Path(self.database_url.replace("sqlite:///", "", 1)).resolve()

    @cached_property
    def storage_path(self) -> Path:
        return Path(self.storage_dir).resolve()

    @cached_property
    def export_path(self) -> Path:
        return Path(self.export_dir).resolve()

    @cached_property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
