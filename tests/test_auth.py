from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_success():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
