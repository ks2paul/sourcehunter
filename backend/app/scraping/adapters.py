from typing import Protocol

from app.scraping.models import RawListing


class SupplierPlatformAdapter(Protocol):
    platform: str

    async def search(self, keyword: str) -> list[RawListing]:
        """Search one supplier platform and return raw, source-backed listings."""
