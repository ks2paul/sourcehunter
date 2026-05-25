import pytest

from app.scraping.models import RawListing, ScrapeFailure
from app.scraping.worker import ScrapingWorker


class SuccessfulAdapter:
    platform = "TestPlatform"

    async def search(self, keyword: str) -> list[RawListing]:
        return [
            RawListing(
                platform=self.platform,
                source_url=f"https://example.test/search?q={keyword}",
                product_url="https://example.test/product/1",
                supplier_url="https://example.test/supplier/a",
                raw_product_name="Handheld Fan",
                raw_company_name="Example Factory",
                raw_price="3.20",
                raw_moq="500",
            )
        ]


class FailingAdapter:
    platform = "FailingPlatform"

    async def search(self, keyword: str) -> list[RawListing]:
        raise RuntimeError("platform blocked request")


@pytest.mark.anyio
async def test_scraping_worker_collects_raw_listings():
    worker = ScrapingWorker(adapters=[SuccessfulAdapter()])

    result = await worker.search_all("handheld fan")

    assert len(result.listings) == 1
    assert result.listings[0].platform == "TestPlatform"
    assert result.listings[0].raw_company_name == "Example Factory"
    assert result.failures == []


@pytest.mark.anyio
async def test_scraping_worker_records_adapter_failures_without_fake_results():
    worker = ScrapingWorker(adapters=[FailingAdapter()])

    result = await worker.search_all("handheld fan")

    assert result.listings == []
    assert result.failures == [
        ScrapeFailure(
            platform="FailingPlatform",
            keyword="handheld fan",
            error_type="RuntimeError",
            message="platform blocked request",
        )
    ]
