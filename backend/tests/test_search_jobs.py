import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import KeywordExpansion, SearchJob, SearchJobCreate, SearchJobStatus, SearchProgress, SupplierPreference, utc_now
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


@pytest.mark.anyio
async def test_search_job_repository_persists_jobs_across_instances(tmp_path):
    db_path = tmp_path / "sourcehunter.sqlite3"
    first_repository = SearchJobRepository(db_path=db_path)
    request = SearchJobCreate(product_keyword="picture frame")

    created = await first_repository.create(request)
    second_repository = SearchJobRepository(db_path=db_path)

    loaded = second_repository.get(created.job_id)
    assert loaded is not None
    assert loaded.job_id == created.job_id
    assert loaded.product_keyword == "picture frame"
    assert "相框" in loaded.keyword_expansion.chinese_keywords


def test_search_job_repository_returns_none_for_missing_job():
    repository = SearchJobRepository()

    assert repository.get("job_missing") is None


def test_search_job_repository_persists_supplier_results(tmp_path):
    repository = SearchJobRepository(db_path=tmp_path / "sourcehunter.sqlite3")
    payload = {
        "status": "completed",
        "suppliers": [{"supplier_id": "sup_1", "company_name": "Supplier A"}],
        "failures": [],
    }

    repository.save_supplier_result("job_1", payload)
    second_repository = SearchJobRepository(db_path=tmp_path / "sourcehunter.sqlite3")

    assert second_repository.get_supplier_result("job_1") == payload


def test_search_job_repository_persists_raw_listing_results(tmp_path):
    repository = SearchJobRepository(db_path=tmp_path / "sourcehunter.sqlite3")
    payload = {
        "status": "completed",
        "listings": [{"platform": "1688", "raw_product_name": "Fan"}],
        "failures": [],
    }

    repository.save_raw_listing_result("job_1", payload)
    second_repository = SearchJobRepository(db_path=tmp_path / "sourcehunter.sqlite3")

    assert second_repository.get_raw_listing_result("job_1") == payload


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


def test_platform_search_keywords_use_english_for_made_in_china_and_chinese_for_1688():
    from app.routes import search_jobs

    job = SearchJob(
        job_id="job_test",
        product_keyword="台式咖啡机",
        target_price=None,
        moq_preference=None,
        supplier_preference=SupplierPreference.FACTORY_PREFERRED,
        status=SearchJobStatus.COMPLETED,
        progress=SearchProgress(stage="completed", message="completed"),
        keyword_expansion=KeywordExpansion(
            english_keywords=["desktop coffee machine"],
            chinese_keywords=["台式咖啡机"],
            variation_keywords=[],
            confidence=0.9,
            source="deterministic_v1",
        ),
        created_at=utc_now(),
        updated_at=utc_now(),
    )

    assert search_jobs._platform_search_keywords(job) == {
        "Made-in-China": "home coffee machine",
        "1688": "台式咖啡机",
    }


def test_get_raw_listings_returns_source_backed_result(monkeypatch):
    from app.scraping.models import RawListing, ScrapeResult
    from app.routes import search_jobs

    class FakeWorker:
        async def search_all(self, keyword: str) -> ScrapeResult:
            assert keyword == "handheld fan"
            return ScrapeResult(
                listings=[
                    RawListing(
                        platform="Made-in-China",
                        source_url="https://www.made-in-china.com/products-search/hot-china-products/Handheld_Fan.html",
                        product_url="https://supplier-a.en.made-in-china.com/product/abc.html",
                        supplier_url="https://supplier-a.en.made-in-china.com/",
                        raw_product_name="Rechargeable Turbo Mini Fan",
                        raw_company_name="Shenzhen Realmark Industrial Co., Ltd.",
                        raw_price="US$3.50-4.50",
                        raw_moq="1,000 Pieces (MOQ)",
                    )
                ],
                failures=[],
            )

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FakeWorker())
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}/raw-listings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == created["job_id"]
    assert payload["status"] == "completed"
    assert payload["listings"][0]["platform"] == "Made-in-China"
    assert payload["listings"][0]["raw_company_name"] == "Shenzhen Realmark Industrial Co., Ltd."
    assert payload["failures"] == []


def test_get_unique_suppliers_deduplicates_raw_listings(monkeypatch):
    from app.scraping.models import RawListing, ScrapeResult
    from app.routes import search_jobs

    class FakeWorker:
        async def search_all(self, keyword: str) -> ScrapeResult:
            assert keyword == "handheld fan"
            return ScrapeResult(
                listings=[
                    RawListing(
                        platform="Made-in-China",
                        source_url="https://www.made-in-china.com/search",
                        product_url="https://supplier-a.en.made-in-china.com/product/one.html",
                        supplier_url="https://supplier-a.en.made-in-china.com/",
                        raw_product_name="Handheld Fan A",
                        raw_company_name="Shenzhen Realmark Industrial Co., Ltd.",
                        raw_price="US$3.50",
                        raw_moq="1,000 Pieces (MOQ)",
                    ),
                    RawListing(
                        platform="Made-in-China",
                        source_url="https://www.made-in-china.com/search",
                        product_url="https://supplier-a.en.made-in-china.com/product/two.html",
                        supplier_url="https://supplier-a.en.made-in-china.com/",
                        raw_product_name="Handheld Fan B",
                        raw_company_name="Shenzhen Realmark Industrial Co., Ltd.",
                        raw_price="US$4.00",
                        raw_moq="500 Pieces (MOQ)",
                    ),
                ],
                failures=[],
            )

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FakeWorker())
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}/suppliers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == created["job_id"]
    assert payload["status"] == "completed"
    assert len(payload["suppliers"]) == 1
    supplier = payload["suppliers"][0]
    assert supplier["supplier_id"].startswith("sup_")
    assert supplier["company_name"] == "Shenzhen Realmark Industrial Co., Ltd."
    assert supplier["listing_count"] == 2
    assert supplier["supplier_type"] == "Supplier Type Unknown"
    assert supplier["supplier_score"] > 0
    assert supplier["recommended_action"]
    assert supplier["recommendation_reasons"]
    assert [product["product_name"] for product in supplier["products"]] == ["Handheld Fan A", "Handheld Fan B"]


def test_get_unique_suppliers_returns_platform_specific_top_five(monkeypatch):
    from app.scraping.models import RawListing, ScrapeResult
    from app.routes import search_jobs

    class FakeWorker:
        async def search_all(self, keyword: str) -> ScrapeResult:
            listings: list[RawListing] = []
            for index in range(6):
                listings.append(
                    RawListing(
                        platform="Made-in-China",
                        source_url="https://www.made-in-china.com/search",
                        product_url=f"https://mic-{index}.example/product.html",
                        supplier_url=f"https://mic-{index}.en.made-in-china.com/",
                        raw_product_name="Rechargeable Handheld Fan",
                        raw_company_name=f"MIC Supplier {index}",
                        raw_price="US$3.50",
                        raw_moq="500 Pieces (MOQ)",
                    )
                )
                listings.append(
                    RawListing(
                        platform="1688",
                        source_url="https://openapi.elim.asia/v1/products/search",
                        product_url=f"https://detail.1688.com/offer/{index}.html",
                        raw_supplier_id=f"shop-{index}",
                        raw_product_name="Rechargeable Handheld Fan",
                        raw_supplier_type="factory",
                        raw_price="¥9.80",
                        raw_moq="20 pieces",
                    )
                )
            return ScrapeResult(listings=listings, failures=[])

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FakeWorker())
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}/suppliers")

    assert response.status_code == 200
    platform_groups = response.json()["platform_supplier_groups"]
    assert [group["platform"] for group in platform_groups] == ["Made-in-China", "1688"]
    assert len(platform_groups[0]["suppliers"]) == 5
    assert len(platform_groups[1]["suppliers"]) == 5
    assert all(supplier["platforms"] == ["Made-in-China"] for supplier in platform_groups[0]["suppliers"])
    assert all(supplier["platforms"] == ["1688"] for supplier in platform_groups[1]["suppliers"])


def test_get_unique_suppliers_honors_factory_only_without_guessing(monkeypatch):
    from app.scraping.models import RawListing, ScrapeResult
    from app.routes import search_jobs

    class FakeWorker:
        async def search_all(self, keyword: str) -> ScrapeResult:
            return ScrapeResult(
                listings=[
                    RawListing(
                        platform="Made-in-China",
                        source_url="https://www.made-in-china.com/search",
                        product_url="https://supplier-a.en.made-in-china.com/product/one.html",
                        supplier_url="https://supplier-a.en.made-in-china.com/",
                        raw_product_name="Handheld Fan A",
                        raw_company_name="Shenzhen Industrial Co., Ltd.",
                        raw_price="US$3.50",
                        raw_moq="1,000 Pieces (MOQ)",
                    )
                ],
                failures=[],
            )

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FakeWorker())
    client = TestClient(app)
    created = client.post(
        "/api/search-jobs",
        json={"product_keyword": "handheld fan", "supplier_preference": "Factory Only"},
    ).json()

    response = client.get(f"/api/search-jobs/{created['job_id']}/suppliers")

    assert response.status_code == 200
    assert response.json()["status"] == "no_results"
    assert response.json()["suppliers"] == []


def test_get_unique_suppliers_uses_cached_result(monkeypatch):
    from app.routes import search_jobs

    class FailingWorker:
        async def search_all(self, keyword: str):
            raise AssertionError("worker should not be called when supplier result is cached")

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FailingWorker())
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()
    search_jobs.repository.save_supplier_result(
        created["job_id"],
        {
            "cache_version": search_jobs.SUPPLIER_CACHE_VERSION,
            "status": "completed",
            "suppliers": [
                {
                    "supplier_id": "sup_cached",
                    "company_name": "Cached Supplier",
                    "supplier_type": "Supplier Type Unknown",
                    "supplier_url": None,
                    "platforms": ["1688"],
                    "listing_count": 1,
                    "supplier_score": 50,
                    "score_breakdown": {},
                    "recommendation_reasons": ["Cached result."],
                    "recommended_action": "Verify supplier details first",
                    "products": [],
                }
            ],
            "platform_supplier_groups": [
                {
                    "platform": "1688",
                    "suppliers": [
                        {
                            "supplier_id": "sup_cached",
                            "company_name": "Cached Supplier",
                            "supplier_type": "Supplier Type Unknown",
                            "supplier_url": None,
                            "platforms": ["1688"],
                            "listing_count": 1,
                            "supplier_score": 50,
                            "score_breakdown": {},
                            "recommendation_reasons": ["Cached result."],
                            "recommended_action": "Verify supplier details first",
                            "products": [],
                        }
                    ],
                }
            ],
            "failures": [],
        },
    )

    response = client.get(f"/api/search-jobs/{created['job_id']}/suppliers")

    assert response.status_code == 200
    assert response.json()["suppliers"][0]["supplier_id"] == "sup_cached"


def test_get_unique_suppliers_refreshes_legacy_cache_without_platform_groups(monkeypatch):
    from app.scraping.models import RawListing, ScrapeResult
    from app.routes import search_jobs

    class FakeWorker:
        async def search_all(self, keyword: str) -> ScrapeResult:
            return ScrapeResult(
                listings=[
                    RawListing(
                        platform="1688",
                        source_url="https://openapi.elim.asia/v1/products/search",
                        product_url="https://detail.1688.com/offer/1.html",
                        raw_supplier_id="shop-1",
                        raw_product_name="Rechargeable Handheld Fan",
                        raw_supplier_type="factory",
                        raw_price="¥9.80",
                        raw_moq="20 pieces",
                    )
                ],
                failures=[],
            )

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FakeWorker())
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()
    search_jobs.repository.save_supplier_result(
        created["job_id"],
        {
            "status": "completed",
            "suppliers": [],
            "failures": [],
        },
    )

    response = client.get(f"/api/search-jobs/{created['job_id']}/suppliers")

    assert response.status_code == 200
    assert response.json()["platform_supplier_groups"][1]["platform"] == "1688"
    assert len(response.json()["platform_supplier_groups"][1]["suppliers"]) == 1


def test_get_unique_suppliers_refreshes_stale_platform_cache(monkeypatch):
    from app.scraping.models import RawListing, ScrapeResult
    from app.routes import search_jobs

    class FakeWorker:
        async def search_all(self, keyword: str) -> ScrapeResult:
            return ScrapeResult(
                listings=[
                    RawListing(
                        platform="Made-in-China",
                        source_url="https://www.made-in-china.com/search",
                        product_url="https://supplier-a.en.made-in-china.com/product/one.html",
                        supplier_url="https://supplier-a.en.made-in-china.com/",
                        raw_product_name="Rechargeable Handheld Fan",
                        raw_company_name="Fresh Made-in-China Supplier",
                        raw_price="US$2.50",
                        raw_moq="100 Pieces (MOQ)",
                    )
                ],
                failures=[],
            )

    monkeypatch.setattr(search_jobs, "create_scraping_worker", lambda: FakeWorker())
    client = TestClient(app)
    created = client.post("/api/search-jobs", json={"product_keyword": "handheld fan"}).json()
    search_jobs.repository.save_supplier_result(
        created["job_id"],
        {
            "status": "completed",
            "suppliers": [],
            "platform_supplier_groups": [
                {"platform": "Made-in-China", "suppliers": []},
                {"platform": "1688", "suppliers": []},
            ],
            "failures": [],
        },
    )

    response = client.get(f"/api/search-jobs/{created['job_id']}/suppliers")

    assert response.status_code == 200
    assert response.json()["cache_version"] == search_jobs.SUPPLIER_CACHE_VERSION
    assert response.json()["platform_supplier_groups"][0]["platform"] == "Made-in-China"
    assert len(response.json()["platform_supplier_groups"][0]["suppliers"]) == 1
