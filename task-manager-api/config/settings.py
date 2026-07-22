import os

from dotenv import load_dotenv


def _as_int(name, default):
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError as error:
        raise RuntimeError(f"{name} deve ser um número inteiro") from error


def _cors_origins():
    value = os.getenv("CORS_ORIGINS", "")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def load_settings():
    load_dotenv()
    return {
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL", "sqlite:///tasks.db"
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "TOKEN_MAX_AGE_SECONDS": _as_int("TOKEN_MAX_AGE_SECONDS", 3600),
        "CORS_ORIGINS": _cors_origins(),
        "HOST": os.getenv("HOST", "127.0.0.1"),
        "PORT": _as_int("PORT", 5000),
        "DEBUG": os.getenv("FLASK_DEBUG", "false").lower() == "true",
        "DEFAULT_PAGE_SIZE": _as_int("DEFAULT_PAGE_SIZE", 50),
        "MAX_PAGE_SIZE": _as_int("MAX_PAGE_SIZE", 100),
    }


def validate_settings(config):
    secret_key = config.get("SECRET_KEY")
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY é obrigatória e deve possuir pelo menos 32 caracteres"
        )

    if config["TOKEN_MAX_AGE_SECONDS"] <= 0:
        raise RuntimeError("TOKEN_MAX_AGE_SECONDS deve ser maior que zero")

    if config["DEFAULT_PAGE_SIZE"] <= 0 or config["MAX_PAGE_SIZE"] <= 0:
        raise RuntimeError("Os limites de paginação devem ser maiores que zero")

    if config["DEFAULT_PAGE_SIZE"] > config["MAX_PAGE_SIZE"]:
        raise RuntimeError("DEFAULT_PAGE_SIZE não pode exceder MAX_PAGE_SIZE")
