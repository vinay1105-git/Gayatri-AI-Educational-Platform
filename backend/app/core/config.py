from functools import lru_cache
from pathlib import Path
from typing import List
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "gayatri_ai.db"
DEFAULT_ML_DIR = BACKEND_DIR / "ml_artifacts"


class Settings(BaseSettings):
    APP_NAME: str = "Gayatri AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"

    ML_ARTIFACTS_DIR: str = str(DEFAULT_ML_DIR)
    LOG_LEVEL: str = "INFO"
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def ml_artifacts_path(self) -> Path:
        path = Path(self.ML_ARTIFACTS_DIR)
        if not path.is_absolute():
            path = (BACKEND_DIR / path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_ML_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
