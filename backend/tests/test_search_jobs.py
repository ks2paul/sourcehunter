import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import SearchJobCreate, SupplierPreference
from app.storage import SearchJobRepository


@pytest.mark.anyio
async def test_search_job_repository_creates_completed_job():
    repository = SearchJobRepository()
    request = SearchJobCreate(
        product_keyword="handheld fan",
        target_price=3.5,
        moq_preference=500,
        supplier_preference=SupplierPreference.FACTORY_PREFERRED,
        product_image_id=None,
    )

    job = await repository.create(request)

    assert job.job_id.startswith("job_")
    assert job.status == "completed"
    assert job.product_keyword == "handheld fan"
    assert job.keyword_expansion.english_keywords[0] == "handheld fan"
    assert "手持风扇" in job.keyword_expansion.chinese_keywords


def test_search_job_repository_returns_none_for_missing_job():
    repository = SearchJobRepository()

    assert repository.get("job_missing") is None


def test_create_search_job_api_returns_job():
    client = TestClient(app)

    response = client.post(
        "/api/search-jobs",
        json={
            "product_keyword": "handheld fan",
            "target_price": 3.5,
            "moq_preference": 500,
            "supplier_preference": "Factory Preferred",
            "product_image_id": None,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["job_id"].startswith("job_")
    assert payload["status"] == "completed"
    assert payload["keyword_expansion"]["english_keywords"][0] == "handheld fan"


def test_get_search_job_api_returns_created_job():
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "picture frame"}).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == created["job_id"]
    assert "相框" in payload["keyword_expansion"]["chinese_keywords"]


def test_get_search_job_api_returns_404_for_missing_job():
    client = TestClient(app)

    response = client.get("/api/search-jobs/job_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Search job not found"


def test_get_raw_listings_returns_empty_foundation_result():
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}/raw-listings")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": created["job_id"],
        "status": "scraping_not_enabled",
        "listings": [],
        "failures": [],
    }
