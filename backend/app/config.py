import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


def load_environment() -> Path | None:
    """
    Load environment variables from backend/.env before Config reads os.getenv.
    Returns the path loaded, or None if .env is missing.
    """
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE, override=True)
        return ENV_FILE
    # Fallback: allow a .env in the process working directory
    load_dotenv(override=True)
    return None


# Load as soon as this module is imported (before Config class attributes).
_ENV_LOADED_FROM = load_environment()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    _default_db = (BASE_DIR / "instance" / "hr_collector.db").as_posix()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_default_db}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

    UPLOAD_FOLDER = BASE_DIR / "uploads"
    RESUME_UPLOAD_FOLDER = UPLOAD_FOLDER / "resumes"
    DOCUMENT_UPLOAD_FOLDER = UPLOAD_FOLDER / "documents"
    INSTANCE_FOLDER = BASE_DIR / "instance"

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "16")) * 1024 * 1024

    ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_MODEL = os.getenv(
        "OPENROUTER_MODEL", "google/gemini-2.0-flash-001"
    )
    OPENROUTER_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "30"))

    @staticmethod
    def init_app(app) -> None:
        load_environment()
        app.config["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "").strip()
        app.config["OPENROUTER_BASE_URL"] = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).strip()
        app.config["OPENROUTER_MODEL"] = os.getenv(
            "OPENROUTER_MODEL", "google/gemini-2.0-flash-001"
        ).strip()
        app.config["OPENROUTER_TIMEOUT"] = float(os.getenv("OPENROUTER_TIMEOUT", "30"))

        for folder in (
            Config.INSTANCE_FOLDER,
            Config.UPLOAD_FOLDER,
            Config.RESUME_UPLOAD_FOLDER,
            Config.DOCUMENT_UPLOAD_FOLDER,
        ):
            folder.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
