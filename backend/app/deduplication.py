from hashlib import sha256
from statistics import median
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.scraping.models import RawListing


class SupplierProduct(BaseModel):
    product_name: str | None
    product_url: str | None
    supplier_id: str | None
    price: str | None
    moq: str | None
    platform: str
    source_url: str


class UniqueSupplier(BaseModel):
    supplier_id: str
    company_name: str
    supplier_type: str
    supplier_url: str | None
    platforms: list[str]
    listing_count: int
    supplier_score: int = Field(ge=0, le=100)
    score_breakdown: dict[str, int]
    recommendation_tier: str
    recommendation_reasons: list[str]
    risk_flags: list[str]
    recommended_action: str
    products: list[SupplierProduct]


def deduplicate_suppliers(
    listings: list[RawListing],
    limit: int = 5,
    product_keyword: str | None = None,
    target_price: float | None = None,
    moq_preference: int | None = None,
    supplier_preference: str | None = None,
) -> list[UniqueSupplier]:
    grouped: dict[str, list[RawListing]] = {}

    for listing in listings:
        identity = _supplier_identity(listing)
        if identity is None:
            continue
        grouped.setdefault(identity, []).append(listing)

    market_median_price = _market_median_price(listings)
    suppliers = [
        _build_supplier(
            identity=identity,
            listings=group,
            product_keyword=product_keyword,
            target_price=target_price,
            moq_preference=moq_preference,
            market_median_price=market_median_price,
        )
        for identity, group in grouped.items()
    ]
    if supplier_preference == "Factory Only":
        suppliers = [supplier for supplier in suppliers if supplier.supplier_type == "Verified Factory"]

    ranked_suppliers = sorted(
        suppliers,
        key=lambda supplier: (-supplier.supplier_score, -supplier.listing_count, supplier.company_name.lower()),
    )
    return ranked_suppliers[:limit]


def _supplier_identity(listing: RawListing) -> str | None:
    supplier_id = _normalize_text(listing.raw_supplier_id)
    if supplier_id:
        return f"supplier_id:{listing.platform.lower()}:{supplier_id}"

    normalized_url = _normalize_url(listing.supplier_url)
    if normalized_url:
        return f"url:{normalized_url}"

    company_name = _normalize_text(listing.raw_company_name)
    if company_name:
        return f"name:{company_name}"

    return None


def _build_supplier(
    identity: str,
    listings: list[RawListing],
    product_keyword: str | None,
    target_price: float | None,
    moq_preference: int | None,
    market_median_price: float | None,
) -> UniqueSupplier:
    company_name = next((listing.raw_company_name for listing in listings if listing.raw_company_name), None)
    supplier_url = next((listing.supplier_url for listing in listings if listing.supplier_url), None)
    platforms = sorted({listing.platform for listing in listings})
    score_breakdown = _score_supplier(
        listings=listings,
        company_name=company_name,
        supplier_url=supplier_url,
        product_keyword=product_keyword,
        target_price=target_price,
        moq_preference=moq_preference,
        market_median_price=market_median_price,
    )
    supplier_score = min(100, sum(score_breakdown.values()))
    supplier_type = _supplier_type(listings)
    risk_flags = _risk_flags(
        listings=listings,
        score_breakdown=score_breakdown,
        product_keyword=product_keyword,
        target_price=target_price,
        market_median_price=market_median_price,
    )
    recommendation_tier = _recommendation_tier(
        supplier_score=supplier_score,
        risk_flags=risk_flags,
    )
    reasons = _recommendation_reasons(
        listings=listings,
        score_breakdown=score_breakdown,
        product_keyword=product_keyword,
        target_price=target_price,
        moq_preference=moq_preference,
        market_median_price=market_median_price,
    )

    return UniqueSupplier(
        supplier_id=_supplier_id(identity),
        company_name=company_name or "Company Name Unavailable",
        supplier_type=supplier_type,
        supplier_url=supplier_url,
        platforms=platforms,
        listing_count=len(listings),
        supplier_score=supplier_score,
        score_breakdown=score_breakdown,
        recommendation_tier=recommendation_tier,
        recommendation_reasons=reasons,
        risk_flags=risk_flags,
        recommended_action=_recommended_action(tier=recommendation_tier, reasons=reasons, risk_flags=risk_flags),
        products=[
            SupplierProduct(
                product_name=listing.raw_product_name,
                product_url=listing.product_url,
                supplier_id=listing.raw_supplier_id,
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


def _score_supplier(
    listings: list[RawListing],
    company_name: str | None,
    supplier_url: str | None,
    product_keyword: str | None,
    target_price: float | None,
    moq_preference: int | None,
    market_median_price: float | None,
) -> dict[str, int]:
    return {
        "category_specialization": min(15, len(listings) * 5),
        "factory_likelihood": _factory_likelihood_score(company_name, listings),
        "price_competitiveness": _price_score(listings, target_price, market_median_price),
        "moq_suitability": _moq_score(listings, moq_preference),
        "export_readiness": _export_readiness_score(listings, supplier_url),
        "business_maturity": _business_maturity_score(listings),
        "product_match_quality": _product_match_score(listings, product_keyword),
    }


def _product_match_score(listings: list[RawListing], product_keyword: str | None) -> int:
    keyword = (product_keyword or "").lower()
    normalized_keyword = re.sub(r"\s+", "", keyword)
    tokens = [token for token in re.split(r"[^a-z0-9]+", keyword) if token]
    if not tokens:
        if not normalized_keyword:
            return 10
        for listing in listings:
            product_name = re.sub(r"\s+", "", (listing.raw_product_name or "").lower())
            if normalized_keyword and normalized_keyword in product_name:
                return 25
        return 10

    best_ratio = 0.0
    for listing in listings:
        product_name = (listing.raw_product_name or "").lower()
        compact_product_name = re.sub(r"\s+", "", product_name)
        if not product_name:
            continue
        matched = sum(1 for token in tokens if token in product_name or token in compact_product_name)
        best_ratio = max(best_ratio, matched / len(tokens))

    return round(best_ratio * 25)


def _price_score(listings: list[RawListing], target_price: float | None, market_median_price: float | None = None) -> int:
    prices = [_parse_lowest_number(listing.raw_price) for listing in listings]
    known_prices = [price for price in prices if price is not None]
    if not known_prices:
        return 0

    lowest_price = min(known_prices)
    if target_price:
        if lowest_price <= target_price:
            return 20
        if lowest_price <= target_price * 1.25:
            return 14
        if lowest_price <= target_price * 1.5:
            return 8
        return 3

    if market_median_price:
        if lowest_price < market_median_price * 0.5:
            return 8
        if lowest_price <= market_median_price:
            return 18
        if lowest_price <= market_median_price * 1.25:
            return 14
        if lowest_price <= market_median_price * 1.5:
            return 10
        return 5

    if lowest_price <= 1:
        return 20
    if lowest_price <= 3:
        return 16
    if lowest_price <= 6:
        return 10
    return 5


def _moq_score(listings: list[RawListing], moq_preference: int | None) -> int:
    moqs = [_parse_lowest_number(listing.raw_moq) for listing in listings]
    known_moqs = [moq for moq in moqs if moq is not None]
    if not known_moqs:
        return 0

    lowest_moq = min(known_moqs)
    if moq_preference:
        if lowest_moq <= moq_preference:
            return 15
        if lowest_moq <= moq_preference * 2:
            return 10
        if lowest_moq <= moq_preference * 5:
            return 5
        return 1

    if lowest_moq <= 50:
        return 15
    if lowest_moq <= 500:
        return 10
    if lowest_moq <= 1000:
        return 5
    return 2


def _export_readiness_score(listings: list[RawListing], supplier_url: str | None) -> int:
    score = 0
    if supplier_url:
        score += 4
    if any(listing.platform == "Made-in-China" for listing in listings):
        score += 4
    if any(listing.raw_contact_text for listing in listings):
        score += 2
    return min(10, score)


def _business_maturity_score(listings: list[RawListing]) -> int:
    years = [_parse_lowest_number(listing.raw_years_in_business) for listing in listings]
    known_years = [year for year in years if year is not None]
    if not known_years:
        return 0
    oldest = max(known_years)
    if oldest >= 10:
        return 10
    if oldest >= 5:
        return 7
    if oldest >= 2:
        return 4
    return 2


def _factory_likelihood_score(company_name: str | None, listings: list[RawListing] | None = None) -> int:
    if listings and any((listing.raw_supplier_type or "").lower() == "factory" for listing in listings):
        return 10
    normalized = _normalize_text(company_name) or ""
    if not normalized:
        return 0
    manufacturer_terms = ("factory", "manufacturing", "industrial", "electronics", "technology", "appliance")
    trader_terms = ("trading", "trade", "import", "export")
    if any(term in normalized for term in trader_terms):
        return 2
    if any(term in normalized for term in manufacturer_terms):
        return 5
    return 1


def _supplier_type(listings: list[RawListing]) -> str:
    supplier_types = {(listing.raw_supplier_type or "").lower() for listing in listings}
    if "factory" in supplier_types:
        return "Verified Factory"
    if "merchant" in supplier_types:
        return "Verified Merchant"
    if "seller" in supplier_types:
        return "Verified Seller"
    return "Supplier Type Unknown"


def _recommendation_reasons(
    listings: list[RawListing],
    score_breakdown: dict[str, int],
    product_keyword: str | None,
    target_price: float | None,
    moq_preference: int | None,
    market_median_price: float | None,
) -> list[str]:
    reasons: list[str] = []
    if product_keyword and score_breakdown["product_match_quality"] >= 20:
        reasons.append("Strong product keyword match.")
    if score_breakdown["category_specialization"] >= 10:
        reasons.append("Multiple matching listings from the same supplier.")
    if score_breakdown["price_competitiveness"] >= 14:
        reasons.append("Listed price appears competitive against the target.")
    if score_breakdown["moq_suitability"] >= 10:
        reasons.append("MOQ appears suitable for the preference.")
    if score_breakdown["export_readiness"] >= 8:
        reasons.append("Supplier has a platform supplier page suitable for export inquiry.")
    if score_breakdown["factory_likelihood"] >= 5:
        reasons.append("Company wording suggests possible manufacturing capability; verify before relying on it.")
    if _price_score(listings, target_price, market_median_price) == 0:
        reasons.append("Price unavailable; ask supplier for current quotation.")
    if _moq_score(listings, moq_preference) == 0:
        reasons.append("MOQ unavailable; confirm MOQ before shortlisting.")
    if not reasons:
        reasons.append("Use as a backup candidate after confirming price, MOQ, and supplier identity.")
    return reasons


def _risk_flags(
    listings: list[RawListing],
    score_breakdown: dict[str, int],
    product_keyword: str | None,
    target_price: float | None,
    market_median_price: float | None,
) -> list[str]:
    flags: list[str] = []
    if product_keyword and (
        score_breakdown["product_match_quality"] < 20 or _looks_like_manual_folding_fan(product_keyword, listings)
    ):
        flags.append("Product title may not match sourcing intent.")

    known_prices = [_parse_lowest_number(listing.raw_price) for listing in listings]
    lowest_price = min((price for price in known_prices if price is not None), default=None)
    if lowest_price is None:
        flags.append("Price unavailable; verify quotation before shortlisting.")
    elif (
        market_median_price
        and lowest_price < market_median_price * 0.5
        and (target_price is None or lowest_price < target_price * 0.5)
    ):
        flags.append("Price is far below market median; verify quotation.")

    known_moqs = [_parse_lowest_number(listing.raw_moq) for listing in listings]
    lowest_moq = min((moq for moq in known_moqs if moq is not None), default=None)
    if lowest_moq is None:
        flags.append("MOQ unavailable; confirm minimum order quantity.")
    elif lowest_moq > 1000:
        flags.append("MOQ is high for trial order.")

    return flags


def _looks_like_manual_folding_fan(product_keyword: str, listings: list[RawListing]) -> bool:
    keyword = product_keyword.lower()
    if "fan" not in keyword or not any(term in keyword for term in ("handheld", "portable", "mini", "rechargeable")):
        return False

    manual_terms = ("bamboo", "folding fan", "paper fan", "hand fan", "wedding fan", "custom printed")
    electric_terms = ("electric", "usb", "rechargeable", "battery", "cooling", "portable", "mini")
    for listing in listings:
        product_name = (listing.raw_product_name or "").lower()
        if any(term in product_name for term in manual_terms) and not any(term in product_name for term in electric_terms):
            return True
    return False


def _recommendation_tier(supplier_score: int, risk_flags: list[str]) -> str:
    if "Product title may not match sourcing intent." in risk_flags:
        return "D"
    if supplier_score >= 70 and not risk_flags:
        return "A"
    if supplier_score >= 60:
        return "B"
    if supplier_score >= 40:
        return "C"
    return "D"


def _recommended_action(tier: str, reasons: list[str], risk_flags: list[str]) -> str:
    if "Product title may not match sourcing intent." in risk_flags:
        return "Do not shortlist until product match is verified"
    if "Price is far below market median; verify quotation." in risk_flags:
        return "Verify price authenticity before contacting"
    if any(reason.startswith("MOQ unavailable") for reason in reasons) or any(reason.startswith("Price unavailable") for reason in reasons):
        return "Ask for quotation and MOQ"
    if tier == "A":
        return "Request quotation immediately"
    if any("MOQ appears" in reason for reason in reasons):
        return "Request samples"
    return "Verify supplier details first"


def _market_median_price(listings: list[RawListing]) -> float | None:
    known_prices = [_parse_lowest_number(listing.raw_price) for listing in listings]
    prices = [price for price in known_prices if price is not None]
    if not prices:
        return None
    return float(median(prices))


def _parse_lowest_number(value: str | None) -> float | None:
    if not value:
        return None
    matches = re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?", value)
    numbers = [float(match.replace(",", "")) for match in matches]
    return min(numbers) if numbers else None
