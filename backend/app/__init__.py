from flask import Flask, jsonify

from app.config import config_by_name
from app.extensions import cors, db
from app.models import Candidate, Document, RequestLog  # noqa: F401 — register models


def _log_env_loaded() -> None:
    from app.config import ENV_FILE, _ENV_LOADED_FROM

    if _ENV_LOADED_FROM:
        print(f"[OpenRouter debug] Loaded environment from: {_ENV_LOADED_FROM}")
    elif ENV_FILE.is_file():
        print(f"[OpenRouter debug] Loaded environment from: {ENV_FILE}")
    else:
        print(f"[OpenRouter debug] No .env file at {ENV_FILE} — using process environment only")


def _ensure_schema() -> None:
    """Add columns introduced after initial deploy (SQLite)."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "request_logs" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("request_logs")}
    if "message_source" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE request_logs "
                "ADD COLUMN message_source VARCHAR(16) NOT NULL DEFAULT 'template'"
            )
        )
        db.session.commit()
        columns = {col["name"] for col in inspector.get_columns("request_logs")}

    if "channel" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE request_logs "
                "ADD COLUMN channel VARCHAR(32) NOT NULL DEFAULT 'email'"
            )
        )
        db.session.commit()
        columns = {col["name"] for col in inspector.get_columns("request_logs")}

    if "recipient" not in columns:
        db.session.execute(
            text("ALTER TABLE request_logs ADD COLUMN recipient VARCHAR(255)")
        )
        db.session.commit()
        columns = {col["name"] for col in inspector.get_columns("request_logs")}

    if "delivery_status" not in columns:
        db.session.execute(
            text("ALTER TABLE request_logs ADD COLUMN delivery_status VARCHAR(32)")
        )
        db.session.commit()


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    env = config_name or app.config.get("ENV", "development")
    config_class = config_by_name.get(env, config_by_name["default"])
    app.config.from_object(config_class)
    config_class.init_app(app)

    db.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    with app.app_context():
        db.create_all()
        _ensure_schema()
        _log_env_loaded()

    register_error_handlers(app)
    register_blueprints(app)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "hr-document-collector"})

    return app


def register_blueprints(app: Flask) -> None:
    from app.routes.candidates import candidates_bp

    app.register_blueprint(candidates_bp, url_prefix="/api/candidates")


def register_error_handlers(app: Flask) -> None:
    from app.utils.errors import AppError
    from app.utils.responses import error_response

    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return error_response(err.message, err.error_code, err.status_code)

    @app.errorhandler(400)
    def bad_request(err):
        return (
            jsonify({"error": "bad_request", "message": getattr(err, "description", str(err))}),
            400,
        )

    @app.errorhandler(404)
    def not_found(err):
        return (
            jsonify({"error": "not_found", "message": getattr(err, "description", "Not found")}),
            404,
        )

    @app.errorhandler(409)
    def conflict(err):
        return (
            jsonify({"error": "conflict", "message": getattr(err, "description", "Conflict")}),
            409,
        )

    @app.errorhandler(413)
    def payload_too_large(_err):
        return (
            jsonify({"error": "file_too_large", "message": "Uploaded file exceeds size limit"}),
            413,
        )

    @app.errorhandler(500)
    def internal_error(_err):
        return jsonify({"error": "internal_error", "message": "Internal server error"}), 500
