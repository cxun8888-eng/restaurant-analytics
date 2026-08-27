from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app


def test_register_session_and_logout():
    email = f"auth-{uuid4().hex}@example.com"
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"email": email, "password": "password123", "display_name": "测试账户"},
        )
        assert registered.status_code == 200
        assert registered.json()["user"]["email"] == email

        current = client.get("/api/auth/me")
        assert current.status_code == 200
        assert current.json()["user"]["display_name"] == "测试账户"

        logged_out = client.post("/api/auth/logout")
        assert logged_out.status_code == 200
        assert client.get("/api/auth/me").status_code == 401


def test_register_rejects_duplicate_email():
    email = f"duplicate-{uuid4().hex}@example.com"
    with TestClient(app) as client:
        payload = {"email": email, "password": "password123", "display_name": "重复测试"}
        assert client.post("/api/auth/register", json=payload).status_code == 200
        assert client.post("/api/auth/register", json=payload).status_code == 409
