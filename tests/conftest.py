import os

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret-that-is-long-enough")
os.environ.setdefault("JWT_EXPIRATION", "30")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AUTH_RATE_LIMIT", "1000")
os.environ.setdefault("APP_ENV", "test")


@pytest.fixture(autouse=True)
def reset_database():
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
