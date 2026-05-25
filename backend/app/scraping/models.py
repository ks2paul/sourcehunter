from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RawListing(BaseModel):
    platform: str
    source_url: str
    product_url: str | None = None
    supplier_url: str | None = None
    raw_product_name: str | None = None
    raw_company_name: str | None = None
    raw_price: str | None = None
    raw_moq: str | None = None
    raw_location: str | None = None
    raw_years_in_business: str | None = None
    raw_contact_text: str | None = None
    scraped_at: datetime = Field(default_factory=utc_now)


class ScrapeFailure(BaseModel):
    platform: str
    keyword: str
    error_type: str
    message: str


class ScrapeResult(BaseModel):
    listings: list[RawListing]
    failures: list[ScrapeFailure]
