import os
import tempfile

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret-that-is-long-enough")
os.environ.setdefault("JWT_EXPIRATION", "30")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AUTH_RATE_LIMIT", "1000")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "OBJECT_STORE_PATH", tempfile.mkdtemp(prefix="uncalificado-objects-")
)
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
os.environ.setdefault("OAUTH_REDIRECT_BASE", "http://127.0.0.1:8000")


@pytest.fixture(autouse=True)
def reset_database():
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
