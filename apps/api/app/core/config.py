import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=False)


class Settings:
    PROJECT_NAME: str = "EV Guardian AI"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./evguardian.db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production-please")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
