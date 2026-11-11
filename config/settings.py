"""Central configuration. Values come from .env; nothing sensitive is hard-coded or logged."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    base_url: str | None = os.getenv("BASE_URL")
    user: str | None = os.getenv("APP_USER")
    password: str | None = os.getenv("APP_PASSWORD")
    login_path: str = os.getenv("LOGIN_PATH", "/login")
    default_timeout_ms: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "15000"))


settings = Settings()
