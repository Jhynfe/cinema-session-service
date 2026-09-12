import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


def make_token(user_id: int) -> str:
    payload = {"sub": str(user_id)}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture()
def auth_headers():
    def _headers(user_id: int) -> dict:
        return {"Authorization": f"Bearer {make_token(user_id)}"}

    return _headers
