"""Reads settings from environment variables (and from backend/.env if it exists).

Secrets such as API keys live ONLY here on the backend. The frontend never sees them.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # the "backend" folder
load_dotenv(BASE_DIR / ".env")


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _clean_origin(value: str) -> str:
    """Forgives common typing slips: spaces, quotes and a trailing slash (https://x.vercel.app/)."""
    return value.strip().strip("\"'").strip().rstrip("/")


def _cors_origins() -> list[str]:
    # Also accepts the singular name CORS_ORIGIN, since that is an easy typo to make.
    raw = os.getenv("CORS_ORIGINS") or os.getenv("CORS_ORIGIN") or "http://localhost:5173,http://127.0.0.1:5173"
    return [o for o in (_clean_origin(x) for x in _split(raw)) if o]


def _cors_regex() -> str:
    value = os.getenv("CORS_ORIGIN_REGEX", "").strip().strip("\"'").strip()
    if not value and os.getenv("APP_ENV", "development") == "production":
        # Deployed default: allow any *.vercel.app site (there are no cookies, only a token the page
        # itself holds, so this is safe for a demo). Set CORS_ORIGIN_REGEX to something else to change it.
        return r"https://.*\.vercel\.app"
    return value


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _database_url() -> str:
    """Render gives a URL starting with postgres:// or postgresql://.
    SQLAlchemy needs to be told which driver to use, so we add it here."""
    url = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'digi_karigari.db'}"
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY") or "dev-only-secret-change-me-please-0123456789"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

    DATABASE_URL: str = _database_url()

    # Which websites may call the API from a browser (your Vercel address goes here).
    CORS_ORIGINS: list[str] = _cors_origins()
    # Optional pattern, e.g. https://.*\.vercel\.app  (lets Vercel preview URLs work too).
    # In production it defaults to allowing any *.vercel.app address.
    CORS_ORIGIN_REGEX: str = _cors_regex()

    UPLOAD_DIR: Path = (BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")).resolve()
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "5"))

    # When true, the sample data is created automatically on startup if the database is empty.
    AUTO_SEED: bool = _flag("AUTO_SEED", False)

    # mock (demo, no key) | gemini | anthropic
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock").strip().lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    AI_MODEL: str = os.getenv("AI_MODEL", "claude-sonnet-5-5").strip()  # model used when AI_PROVIDER=anthropic


settings = Settings()

# Refuse to run a deployed server with the well-known development secret.
if settings.APP_ENV == "production" and not os.getenv("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY must be set when APP_ENV=production.")
