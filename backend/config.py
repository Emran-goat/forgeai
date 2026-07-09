"""Application configuration using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ForgeAI application settings."""

    model_config = SettingsConfigDict(
        env_prefix="FORGEAI_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    data_dir: Path = Path("data")
    db_path: Path = Path("data/forgeai.db")
    rocm_visible_devices: str = "0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    fireworks_api_key: str = ""


settings = Settings()
