from flask import Flask, jsonify, request

from .auth import router as auth_router
from .auth_middleware import register_auth_middleware
from .config import get_settings
from .contracting import appointments, changes, proposals
from .database import Base, engine
from .errors import register_error_handlers
from .explore import router as explore_router
from .privacy import admin, files, privacy
from .projects import router as projects_router
from .providers import router as providers_router
from .users import router as users_router


def _init_schema() -> None:
    if get_settings().database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["API_TITLE"] = "UnCalificado API"
    app.config["API_VERSION"] = "1.0.0"

    _init_schema()
    register_error_handlers(app)
    register_auth_middleware(app)

    prefixes = (("/api/v1", ""), ("/api", "_compat"))
    blueprints = (
        (auth_router, "/auth"),
        (users_router, "/users"),
        (providers_router, "/providers"),
        (projects_router, "/requests"),
        (appointments, "/appointments"),
        (proposals, "/proposals"),
        (changes, "/changes"),
        (privacy, "/privacy"),
        (admin, "/admin"),
        (files, "/files"),
        (explore_router, "/explore"),
    )
    for blueprint, suffix in blueprints:
        for prefix, name_suffix in prefixes:
            app.register_blueprint(
                blueprint,
                name=f"{blueprint.name}{name_suffix}",
                url_prefix=f"{prefix}{suffix}",
            )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.after_request
    def add_cors(response):
        origin = request.headers.get("Origin", "")
        allowed = {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            get_settings().frontend_origin,
        }
        if origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
        return response

    return app


app = create_app()
