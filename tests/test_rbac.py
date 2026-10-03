from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(username, password):
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password
        }
    )

    return response.json()["access_token"]


def test_admin_can_access_admin_endpoint():
    token = get_token("admin", "admin123")

    response = client.get(
        "/admin",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200


def test_user_cannot_access_admin_endpoint():
    token = get_token("user", "user123")

    response = client.get(
        "/admin",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_invalid_token_rejected():
    response = client.get(
        "/admin",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
