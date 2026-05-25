from app.scraping.adapters import SupplierPlatformAdapter
from app.scraping.models import ScrapeFailure, ScrapeResult


class ScrapingWorker:
    def __init__(self, adapters: list[SupplierPlatformAdapter]) -> None:
        self.adapters = adapters

    async def search_all(self, keyword: str) -> ScrapeResult:
        listings = []
        failures: list[ScrapeFailure] = []

        for adapter in self.adapters:
            try:
                listings.extend(await adapter.search(keyword))
            except Exception as exc:
                failures.append(
                    ScrapeFailure(
                        platform=adapter.platform,
                        keyword=keyword,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        return ScrapeResult(listings=listings, failures=failures)
