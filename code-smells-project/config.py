import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _as_boolean(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    DATABASE = os.getenv("DATABASE_PATH", str(BASE_DIR / "loja.db"))
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
    DEBUG = _as_boolean(os.getenv("FLASK_DEBUG"))
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    CORS_ORIGINS = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    )
    SEED_PASSWORDS = {
        "admin": os.getenv("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(24),
        "joao": os.getenv("SEED_USER_PASSWORD") or secrets.token_urlsafe(24),
        "maria": os.getenv("SEED_SECOND_USER_PASSWORD") or secrets.token_urlsafe(24),
    }
