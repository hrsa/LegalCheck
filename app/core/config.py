import sys

from pydantic_settings import BaseSettings
import os
from typing import Optional

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings, env_file=os.getenv("ENV_FILE", ".env"), case_sensitive=True, extra='allow'):

    @property
    def TESTING(self):
        return 'pytest' in sys.modules

    PROJECT_NAME: str = "LegalCheck"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = os.path.join(BASE, "logs/app.log")
    BASE_DIR: str = BASE
    SECRET_KEY: str
    APP_ENV: str

    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    SENTRY_DSN_URL: Optional[str] = None
    INITIAL_ANALYSIS_PROMPT: str

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 36000

    UPLOAD_DIR: str = "uploads"
    DOCUMENT_STORAGE_PATH: str = os.path.join(UPLOAD_DIR, "documents")
    POLICY_STORAGE_PATH: str = os.path.join(UPLOAD_DIR, "policies")

    @property
    def DATABASE_URL(self) -> str:
        if self.TESTING:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/test_{self.DB_NAME}"

        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
