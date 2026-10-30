from flask import Flask, jsonify

from .auth import router as auth_router
from .auth_middleware import register_auth_middleware
from .database import Base, engine
from .models import User
from .security import get_current_user


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["API_TITLE"] = "UnCalificado API"
    app.config["API_VERSION"] = "0.1.0"

    Base.metadata.create_all(bind=engine)
    register_auth_middleware(app)
    app.register_blueprint(auth_router, url_prefix="/api/v1/auth")
    app.register_blueprint(
        auth_router, name="auth_compat", url_prefix="/api/auth"
    )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/v1/users/me")
    @app.get("/api/users/me")
    def current_user_compatibility():
        user = get_current_user()
        return jsonify(
            {
                "id": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "status": user.status.value,
                "privacy_consent_version": user.privacy_consent_version,
                "created_at": user.created_at.isoformat(),
            }
        )

    return app


app = create_app()
