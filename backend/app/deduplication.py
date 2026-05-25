from hashlib import sha256
from urllib.parse import urlparse

from pydantic import BaseModel

from app.scraping.models import RawListing


class SupplierProduct(BaseModel):
    product_name: str | None
    product_url: str | None
    price: str | None
    moq: str | None
    platform: str
    source_url: str


class UniqueSupplier(BaseModel):
    supplier_id: str
    company_name: str
    supplier_url: str | None
    platforms: list[str]
    listing_count: int
    products: list[SupplierProduct]


def deduplicate_suppliers(listings: list[RawListing], limit: int = 5) -> list[UniqueSupplier]:
    grouped: dict[str, list[RawListing]] = {}

    for listing in listings:
        identity = _supplier_identity(listing)
        if identity is None:
            continue
        grouped.setdefault(identity, []).append(listing)

    suppliers = [_build_supplier(identity, group) for identity, group in grouped.items()]
    ranked_suppliers = sorted(suppliers, key=lambda supplier: (-supplier.listing_count, supplier.company_name.lower()))
    return ranked_suppliers[:limit]


def _supplier_identity(listing: RawListing) -> str | None:
    normalized_url = _normalize_url(listing.supplier_url)
    if normalized_url:
        return f"url:{normalized_url}"

    company_name = _normalize_text(listing.raw_company_name)
    if company_name:
        return f"name:{company_name}"

    return None


def _build_supplier(identity: str, listings: list[RawListing]) -> UniqueSupplier:
    first = listings[0]
    company_name = next((listing.raw_company_name for listing in listings if listing.raw_company_name), None)
    supplier_url = next((listing.supplier_url for listing in listings if listing.supplier_url), None)
    platforms = sorted({listing.platform for listing in listings})

    return UniqueSupplier(
        supplier_id=_supplier_id(identity),
        company_name=company_name or "Company Name Unavailable",
        supplier_url=supplier_url,
        platforms=platforms,
        listing_count=len(listings),
        products=[
            SupplierProduct(
                product_name=listing.raw_product_name,
                product_url=listing.product_url,
                price=listing.raw_price,
                moq=listing.raw_moq,
                platform=listing.platform,
                source_url=listing.source_url,
            )
            for listing in listings
        ],
    )


def _supplier_id(identity: str) -> str:
    return f"sup_{sha256(identity.encode('utf-8')).hexdigest()[:16]}"


def _normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    path = parsed.path.rstrip("/")
    return f"{parsed.netloc.lower()}{path}"


def _normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(value.lower().split()) or None
