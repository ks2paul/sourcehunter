from fastapi.testclient import TestClient

from app.main import app


def test_login_accepts_admin_credentials():
    client = TestClient(app)

    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
    assert "sourcehunter_session" in response.cookies


def test_login_rejects_unknown_credentials():
    client = TestClient(app)

    response = client.post("/api/auth/login", json={"username": "other", "password": "admin123"})

    assert response.status_code == 401


def test_search_jobs_require_login():
    client = TestClient(app)

    response = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"})

    assert response.status_code == 401


def test_me_returns_logged_in_user():
    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
