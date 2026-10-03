from fastapi.testclient import TestClient
from app.main import app
from app.services.redis import redis_client
from unittest.mock import patch
import pytest

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_redis():
    redis_client.delete("rate_limit:user")
    redis_client.delete("chat:what is ai?")
    redis_client.delete("chat:rate limit automated test")


def get_token():
    response = client.post(
        "/auth/login",
        json={"username": "user", "password": "user123"}
    )
    return response.json()["access_token"]


def test_chat_requires_authentication():
    response = client.post(
        "/chat",
        json={"question": "What is AI?"}
    )
    assert response.status_code == 401


def test_chat_with_invalid_token():
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer invalid_token"},
        json={"question": "What is AI?"}
    )
    assert response.status_code == 401


@patch(
    "app.main.ask_llm",
    return_value={
        "answer": "AI is the simulation of human intelligence by machines.",
        "prompt_tokens": 5,
        "completion_tokens": 10,
        "total_tokens": 15
    }
)
def test_chat_success(mock_llm):
    token = get_token()

    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What is AI?"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "What is AI?"
    assert data["answer"] == "AI is the simulation of human intelligence by machines."

    mock_llm.assert_called_once_with("What is AI?")


@patch(
    "app.main.ask_llm",
    return_value={
        "answer": "Rate limit test answer",
        "prompt_tokens": 5,
        "completion_tokens": 10,
        "total_tokens": 15
    }
)
def test_chat_rate_limit(mock_llm):
    token = get_token()

    for _ in range(10):
        response = client.post(
            "/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"question": "Rate limit automated test"}
        )
        assert response.status_code == 200

    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Rate limit automated test"}
    )

    assert response.status_code == 429