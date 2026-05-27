from hashlib import sha256
from statistics import median
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.scraping.models import RawListing
from app.sourcing_intent import looks_like_raw_material_result


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
    product_features: str | None = None,
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
            product_features=product_features,
            target_price=target_price,
            moq_preference=moq_preference,
            market_median_price=market_median_price,
        )
        for identity, group in grouped.items()
    ]
    suppliers = [supplier for supplier in suppliers if not _has_hard_mismatch(supplier)]
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
    product_features: str | None,
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
        product_features=product_features,
        target_price=target_price,
        moq_preference=moq_preference,
        market_median_price=market_median_price,
    )
    supplier_type = _supplier_type(listings)
    risk_flags = _risk_flags(
        listings=listings,
        score_breakdown=score_breakdown,
        product_keyword=product_keyword,
        target_price=target_price,
        market_median_price=market_median_price,
    )
    supplier_score = _final_supplier_score(score_breakdown=score_breakdown, risk_flags=risk_flags)
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
        company_name=company_name or _supplier_display_fallback(listings),
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


def _supplier_display_fallback(listings: list[RawListing]) -> str:
    product_name = next((listing.raw_product_name for listing in listings if listing.raw_product_name), None)
    platform = next((listing.platform for listing in listings if listing.platform), None)
    if product_name and platform == "1688":
        return product_name
    supplier_id = next((listing.raw_supplier_id for listing in listings if listing.raw_supplier_id), None)
    if supplier_id and platform == "1688":
        return f"1688 Shop ID: {supplier_id}"
    if supplier_id:
        return f"Supplier ID: {supplier_id}"
    return "Company Name Unavailable"


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
    product_features: str | None,
    target_price: float | None,
    moq_preference: int | None,
    market_median_price: float | None,
) -> dict[str, int]:
    platform = _primary_platform(listings)
    if platform == "1688":
        return {
            "category_specialization": min(10, len(listings) * 4),
            "factory_likelihood": _factory_likelihood_score(company_name, listings, max_score=20),
            "price_competitiveness": _price_score(listings, target_price, market_median_price, max_score=20),
            "moq_suitability": _moq_score(listings, moq_preference, max_score=15),
            "supplier_identity": _supplier_identity_score(listings),
            "business_maturity": 0,
            "product_match_quality": _product_match_score(listings, product_keyword),
            "feature_match": _feature_match_score(listings, product_features),
        }

    return {
        "category_specialization": min(10, len(listings) * 4),
        "factory_likelihood": _factory_likelihood_score(company_name, listings, max_score=20),
        "price_competitiveness": _price_score(listings, target_price, market_median_price, max_score=15),
        "moq_suitability": _moq_score(listings, moq_preference, max_score=10),
        "export_readiness": _export_readiness_score(listings, supplier_url),
        "business_maturity": _business_maturity_score(listings),
        "product_match_quality": _product_match_score(listings, product_keyword),
        "feature_match": _feature_match_score(listings, product_features),
    }


def _final_supplier_score(score_breakdown: dict[str, int], risk_flags: list[str]) -> int:
    score = min(100, sum(score_breakdown.values()))
    if "Requested device model is not visible in the product title." in risk_flags:
        score -= 50
    if "Listing appears to be tooling or equipment rather than the requested finished accessory." in risk_flags:
        score -= 45
    if "Listing appears to be raw material rather than a finished product." in risk_flags:
        score -= 35
    if "Product title may not match sourcing intent." in risk_flags:
        score -= 20
    return max(0, score)


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


def _feature_match_score(listings: list[RawListing], product_features: str | None) -> int:
    tokens = _feature_tokens(product_features)
    if not tokens:
        return 0

    best_ratio = 0.0
    for listing in listings:
        product_name = (listing.raw_product_name or "").lower()
        compact_product_name = re.sub(r"\s+", "", product_name)
        if not product_name:
            continue
        matched = sum(1 for token in tokens if token in product_name or token in compact_product_name)
        best_ratio = max(best_ratio, matched / len(tokens))
    return round(best_ratio * 10)


def _feature_tokens(product_features: str | None) -> list[str]:
    if not product_features:
        return []
    normalized = product_features.lower()
    raw_tokens = re.split(r"[,;/，、\s]+", normalized)
    tokens = [token.strip() for token in raw_tokens if token.strip()]
    compact = re.sub(r"[,;/，、\s]+", "", normalized)
    if compact and not tokens:
        tokens.append(compact)
    return tokens[:8]


def _price_score(
    listings: list[RawListing],
    target_price: float | None,
    market_median_price: float | None = None,
    max_score: int = 20,
) -> int:
    prices = [_parse_lowest_number(listing.raw_price) for listing in listings]
    known_prices = [price for price in prices if price is not None]
    if not known_prices:
        return 0

    lowest_price = min(known_prices)
    if target_price:
        if lowest_price <= target_price:
            return max_score
        if lowest_price <= target_price * 1.25:
            return round(max_score * 0.7)
        if lowest_price <= target_price * 1.5:
            return round(max_score * 0.4)
        return max(1, round(max_score * 0.15))

    if market_median_price:
        if lowest_price < market_median_price * 0.5:
            return round(max_score * 0.4)
        if lowest_price <= market_median_price:
            return round(max_score * 0.9)
        if lowest_price <= market_median_price * 1.25:
            return round(max_score * 0.7)
        if lowest_price <= market_median_price * 1.5:
            return round(max_score * 0.5)
        return round(max_score * 0.25)

    if lowest_price <= 1:
        return max_score
    if lowest_price <= 3:
        return round(max_score * 0.8)
    if lowest_price <= 6:
        return round(max_score * 0.5)
    return round(max_score * 0.25)


def _moq_score(listings: list[RawListing], moq_preference: int | None, max_score: int = 15) -> int:
    moqs = [_parse_lowest_number(listing.raw_moq) for listing in listings]
    known_moqs = [moq for moq in moqs if moq is not None]
    if not known_moqs:
        return 0

    lowest_moq = min(known_moqs)
    if moq_preference:
        if lowest_moq <= moq_preference:
            return max_score
        if lowest_moq <= moq_preference * 2:
            return round(max_score * 0.67)
        if lowest_moq <= moq_preference * 5:
            return round(max_score * 0.33)
        return 1

    if lowest_moq <= 50:
        return max_score
    if lowest_moq <= 500:
        return round(max_score * 0.67)
    if lowest_moq <= 1000:
        return round(max_score * 0.33)
    return 2


def _export_readiness_score(listings: list[RawListing], supplier_url: str | None) -> int:
    score = 0
    if supplier_url:
        score += 6
    if any(listing.platform == "Made-in-China" for listing in listings):
        score += 6
    if any(listing.raw_contact_text for listing in listings):
        score += 3
    return min(15, score)


def _business_maturity_score(listings: list[RawListing]) -> int:
    years = [_parse_lowest_number(listing.raw_years_in_business) for listing in listings]
    known_years = [year for year in years if year is not None]
    if not known_years:
        return 0
    oldest = max(known_years)
    if oldest >= 10:
        return 5
    if oldest >= 5:
        return 4
    if oldest >= 2:
        return 2
    return 1


def _factory_likelihood_score(
    company_name: str | None,
    listings: list[RawListing] | None = None,
    max_score: int = 20,
) -> int:
    if listings and any((listing.raw_supplier_type or "").lower() == "factory" for listing in listings):
        return max_score
    if listings and _has_1688_factory_signal(listings):
        return round(max_score * 0.7)
    normalized = _normalize_text(company_name) or ""
    if not normalized:
        return 0
    manufacturer_terms = ("factory", "manufacturing", "industrial", "electronics", "technology", "appliance")
    trader_terms = ("trading", "trade", "import", "export")
    if any(term in normalized for term in trader_terms):
        return round(max_score * 0.2)
    if any(term in normalized for term in manufacturer_terms):
        return round(max_score * 0.6)
    return round(max_score * 0.1)


def _supplier_identity_score(listings: list[RawListing]) -> int:
    if any(listing.raw_company_name for listing in listings):
        return 10
    if any(listing.supplier_url for listing in listings):
        return 8
    if any(listing.raw_supplier_id for listing in listings):
        return 6
    return 0


def _primary_platform(listings: list[RawListing]) -> str:
    platforms = {listing.platform for listing in listings}
    if platforms == {"1688"}:
        return "1688"
    if platforms == {"Made-in-China"}:
        return "Made-in-China"
    return "Mixed"


def _supplier_type(listings: list[RawListing]) -> str:
    supplier_types = {(listing.raw_supplier_type or "").lower() for listing in listings}
    if "factory" in supplier_types:
        return "Verified Factory"
    if _has_1688_factory_signal(listings):
        return "Factory Signal (Unverified)"
    if "merchant" in supplier_types:
        return "Verified Merchant"
    if "seller" in supplier_types:
        return "Verified Seller"
    return "Supplier Type Unknown"


def _has_1688_factory_signal(listings: list[RawListing]) -> bool:
    if not any(listing.platform == "1688" for listing in listings):
        return False
    factory_terms = (
        "源头工厂",
        "源头厂家",
        "生产厂家",
        "厂家直销",
        "厂家供应",
        "工厂",
        "厂家",
        "oem",
        "odm",
        "代工",
        "加工定制",
        "logo定制",
        "可印logo",
    )
    for listing in listings:
        product_name = (listing.raw_product_name or "").lower()
        if any(term in product_name for term in factory_terms):
            return True
    return False


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
    if score_breakdown.get("feature_match", 0) >= 7:
        reasons.append("Requested product features appear in the listing title.")
    if score_breakdown["category_specialization"] >= 10:
        reasons.append("Multiple matching listings from the same supplier.")
    if score_breakdown["price_competitiveness"] >= 14:
        reasons.append("Listed price appears competitive against the target.")
    if score_breakdown["moq_suitability"] >= 10:
        reasons.append("MOQ appears suitable for the preference.")
    if score_breakdown.get("export_readiness", 0) >= 12:
        reasons.append("Supplier has a platform supplier page suitable for export inquiry.")
    if score_breakdown["factory_likelihood"] >= 14:
        if _has_1688_factory_signal(listings):
            reasons.append("1688 title contains factory or OEM signal; verify before relying on it.")
        else:
            reasons.append("Supplier profile shows strong factory signal.")
    if score_breakdown.get("supplier_identity", 0) >= 6:
        reasons.append("1688 supplier identity is available for deduplication.")
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
    if product_keyword and _requested_phone_case(product_keyword) and not _matches_requested_device_model(product_keyword, listings):
        flags.append("Requested device model is not visible in the product title.")
    if product_keyword and _requested_phone_case(product_keyword) and _looks_like_phone_case_equipment(listings):
        flags.append("Listing appears to be tooling or equipment rather than the requested finished accessory.")
    if listings and all(looks_like_raw_material_result(listing.raw_product_name) for listing in listings):
        flags.append("Listing appears to be raw material rather than a finished product.")

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


def _has_hard_mismatch(supplier: UniqueSupplier) -> bool:
    hard_mismatch_flags = {
        "Requested device model is not visible in the product title.",
        "Listing appears to be tooling or equipment rather than the requested finished accessory.",
    }
    return any(flag in hard_mismatch_flags for flag in supplier.risk_flags)


def _requested_phone_case(product_keyword: str) -> bool:
    normalized = product_keyword.lower()
    compact = re.sub(r"\s+", "", normalized)
    return ("phone case" in normalized or "mobile phone case" in normalized or "手机壳" in compact or "保护壳" in compact) and (
        "iphone" in normalized or "apple" in normalized or "苹果" in normalized
    )


def _matches_requested_device_model(product_keyword: str, listings: list[RawListing]) -> bool:
    requested = _iphone_model_requirements(product_keyword)
    if requested is None:
        return True
    for listing in listings:
        title = (listing.raw_product_name or "").lower()
        compact_title = re.sub(r"[^a-z0-9]+", "", title)
        if "iphone" not in compact_title and "apple" not in compact_title:
            continue
        if requested["series"] not in compact_title:
            continue
        if requested["pro"] and "pro" not in compact_title:
            continue
        if requested["max"] and "max" not in compact_title:
            continue
        if _conflicting_iphone_series(compact_title, requested["series"]) and requested["series"] not in compact_title:
            continue
        return True
    return False


def _iphone_model_requirements(product_keyword: str) -> dict[str, object] | None:
    normalized = product_keyword.lower()
    compact = re.sub(r"[^a-z0-9]+", "", normalized)
    match = re.search(r"iphone\s*(\d{1,2})|iphone(\d{1,2})|苹果\s*(\d{1,2})", normalized)
    series = (match.group(1) or match.group(2) or match.group(3)) if match else None
    if not series:
        compact_match = re.search(r"iphone(\d{1,2})", compact)
        series = compact_match.group(1) if compact_match else None
    if not series:
        return None
    return {
        "series": str(series),
        "pro": "pro" in compact,
        "max": "max" in compact,
    }


def _conflicting_iphone_series(compact_title: str, requested_series: str) -> bool:
    series_numbers = set(re.findall(r"iphone(\d{1,2})|apple(\d{1,2})", compact_title))
    flattened = {number for pair in series_numbers for number in pair if number}
    return bool(flattened and requested_series not in flattened)


def _looks_like_phone_case_equipment(listings: list[RawListing]) -> bool:
    equipment_terms = ("mold", "mould", "printer", "printing machine", "heat press", "making machine", "injection mould")
    for listing in listings:
        title = (listing.raw_product_name or "").lower()
        if any(term in title for term in equipment_terms):
            return True
    return False


def _recommendation_tier(supplier_score: int, risk_flags: list[str]) -> str:
    if "Listing appears to be raw material rather than a finished product." in risk_flags:
        return "D"
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
    if "Listing appears to be raw material rather than a finished product." in risk_flags:
        return "Do not shortlist raw material listings for finished-product sourcing"
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
