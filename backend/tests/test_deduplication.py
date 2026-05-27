from app.deduplication import deduplicate_suppliers
from app.scraping.models import RawListing


def test_deduplicate_suppliers_groups_same_supplier_url():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://supplier-a.en.made-in-china.com/product/one.html",
            supplier_url="https://supplier-a.en.made-in-china.com/",
            raw_product_name="Handheld Fan A",
            raw_company_name="Shenzhen Realmark Industrial Co., Ltd.",
            raw_price="US$3.50-4.50",
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
    ]

    suppliers = deduplicate_suppliers(listings)

    assert len(suppliers) == 1
    assert suppliers[0].company_name == "Shenzhen Realmark Industrial Co., Ltd."
    assert suppliers[0].supplier_url == "https://supplier-a.en.made-in-china.com/"
    assert suppliers[0].listing_count == 2
    assert suppliers[0].products[0].supplier_id is None
    assert [product.product_name for product in suppliers[0].products] == ["Handheld Fan A", "Handheld Fan B"]


def test_deduplicate_suppliers_generates_stable_supplier_ids_independent_of_order():
    first = RawListing(
        platform="Made-in-China",
        source_url="https://www.made-in-china.com/search",
        product_url="https://supplier-a.en.made-in-china.com/product/one.html",
        supplier_url="https://supplier-a.en.made-in-china.com/",
        raw_product_name="Handheld Fan A",
        raw_company_name="Shenzhen Realmark Industrial Co., Ltd.",
    )
    second = RawListing(
        platform="Made-in-China",
        source_url="https://www.made-in-china.com/search",
        product_url="https://supplier-b.en.made-in-china.com/product/one.html",
        supplier_url="https://supplier-b.en.made-in-china.com/",
        raw_product_name="Desk Fan",
        raw_company_name="Foshan EBM Technology Co., Ltd.",
    )

    suppliers_a = deduplicate_suppliers([first, second])
    suppliers_b = deduplicate_suppliers([second, first])

    ids_a = {supplier.company_name: supplier.supplier_id for supplier in suppliers_a}
    ids_b = {supplier.company_name: supplier.supplier_id for supplier in suppliers_b}
    assert ids_a == ids_b
    assert all(supplier_id.startswith("sup_") for supplier_id in ids_a.values())


def test_deduplicate_suppliers_skips_listings_without_supplier_identity():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://example.test/product.html",
            raw_product_name="Unknown Fan",
            raw_price="US$3.00",
        )
    ]

    assert deduplicate_suppliers(listings) == []


def test_deduplicate_suppliers_returns_top_five_ranked_by_listing_count():
    listings: list[RawListing] = []
    for supplier_number in range(6):
        listing_total = supplier_number + 1
        for listing_number in range(listing_total):
            listings.append(
                RawListing(
                    platform="Made-in-China",
                    source_url="https://www.made-in-china.com/search",
                    product_url=f"https://supplier-{supplier_number}.example/product-{listing_number}.html",
                    supplier_url=f"https://supplier-{supplier_number}.en.made-in-china.com/",
                    raw_product_name=f"Fan {supplier_number}-{listing_number}",
                    raw_company_name=f"Supplier {supplier_number}",
                )
            )

    suppliers = deduplicate_suppliers(listings)

    assert len(suppliers) == 5
    assert [supplier.company_name for supplier in suppliers] == [
        "Supplier 5",
        "Supplier 4",
        "Supplier 3",
        "Supplier 2",
        "Supplier 1",
    ]


def test_deduplicate_suppliers_ranks_by_score_before_listing_count():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://expensive.example/product-one.html",
            supplier_url="https://expensive.en.made-in-china.com/",
            raw_product_name="General Cooling Fan",
            raw_company_name="High MOQ Supplier",
            raw_price="US$9.00",
            raw_moq="1,000 Pieces (MOQ)",
        ),
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://expensive.example/product-two.html",
            supplier_url="https://expensive.en.made-in-china.com/",
            raw_product_name="Desktop Cooling Fan",
            raw_company_name="High MOQ Supplier",
            raw_price="US$8.50",
            raw_moq="800 Pieces (MOQ)",
        ),
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://best.example/product.html",
            supplier_url="https://best.en.made-in-china.com/",
            raw_product_name="Rechargeable Handheld Fan",
            raw_company_name="Best Match Supplier",
            raw_price="US$2.20-2.80",
            raw_moq="20 Pieces (MOQ)",
        ),
    ]

    suppliers = deduplicate_suppliers(
        listings,
        product_keyword="handheld fan",
        target_price=3.0,
        moq_preference=100,
    )

    assert suppliers[0].company_name == "Best Match Supplier"
    assert suppliers[0].supplier_score > suppliers[1].supplier_score
    assert suppliers[0].recommended_action == "Request quotation immediately"
    assert "Strong product keyword match." in suppliers[0].recommendation_reasons


def test_deduplicate_suppliers_exposes_scoring_components_without_inventing_unknown_type():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://supplier.example/product.html",
            supplier_url="https://supplier.en.made-in-china.com/",
            raw_product_name="Handheld Fan",
            raw_company_name="Supplier With Unknown Type",
            raw_price=None,
            raw_moq=None,
        )
    ]

    supplier = deduplicate_suppliers(listings, product_keyword="handheld fan")[0]

    assert supplier.supplier_type == "Supplier Type Unknown"
    assert 0 <= supplier.supplier_score <= 100
    assert supplier.score_breakdown["price_competitiveness"] == 0
    assert supplier.score_breakdown["moq_suitability"] == 0
    assert "Price unavailable; ask supplier for current quotation." in supplier.recommendation_reasons


def test_deduplicate_suppliers_returns_no_unverified_suppliers_for_factory_only():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://supplier.example/product.html",
            supplier_url="https://supplier.en.made-in-china.com/",
            raw_product_name="Handheld Fan",
            raw_company_name="Shenzhen Industrial Co., Ltd.",
            raw_price="US$2.00",
            raw_moq="20 Pieces (MOQ)",
        )
    ]

    assert deduplicate_suppliers(listings, product_keyword="handheld fan", supplier_preference="Factory Only") == []


def test_deduplicate_suppliers_factory_only_excludes_verified_non_factories():
    listings = [
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/1.html",
            raw_supplier_id="merchant-shop",
            raw_product_name="Handheld Fan",
            raw_company_name=None,
            raw_supplier_type="merchant",
        ),
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/2.html",
            raw_supplier_id="factory-shop",
            raw_product_name="Handheld Fan",
            raw_company_name=None,
            raw_supplier_type="factory",
        ),
    ]

    suppliers = deduplicate_suppliers(listings, product_keyword="handheld fan", supplier_preference="Factory Only")

    assert len(suppliers) == 1
    assert suppliers[0].supplier_type == "Verified Factory"
    assert suppliers[0].products[0].supplier_id == "factory-shop"


def test_deduplicate_suppliers_uses_1688_product_title_when_company_name_is_unavailable():
    listings = [
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/1.html",
            raw_supplier_id="BBBwxiV369psG7ltr3FcivHAQ",
            raw_product_name="洗发水沐浴露套装",
            raw_company_name=None,
            raw_supplier_type="seller",
        )
    ]

    supplier = deduplicate_suppliers(listings, product_keyword="洗发水")[0]

    assert supplier.company_name == "洗发水沐浴露套装"


def test_deduplicate_suppliers_boosts_unverified_1688_factory_title_signal():
    listings = [
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/1.html",
            raw_supplier_id="seller-factory-signal",
            raw_product_name="源头工厂手持风扇便携式口袋迷你usb充电 可OEM",
            raw_supplier_type="seller",
            raw_price="¥9.80",
            raw_moq="20 pieces",
        ),
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/2.html",
            raw_supplier_id="merchant-no-signal",
            raw_product_name="手持风扇便携式口袋迷你usb充电",
            raw_supplier_type="merchant",
            raw_price="¥9.80",
            raw_moq="20 pieces",
        ),
    ]

    suppliers = deduplicate_suppliers(listings, product_keyword="手持风扇")

    assert suppliers[0].products[0].supplier_id == "seller-factory-signal"
    assert suppliers[0].supplier_type == "Factory Signal (Unverified)"
    assert suppliers[0].score_breakdown["factory_likelihood"] == 7


def test_deduplicate_suppliers_flags_product_mismatch():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://supplier.example/product.html",
            supplier_url="https://supplier.en.made-in-china.com/",
            raw_product_name="Factory OEM Hand Held Folding Fans Custom Printed Bamboo Large Hand Fan",
            raw_company_name="Bamboo Gift Supplier",
            raw_price="US$0.80",
            raw_moq="100 Pieces (MOQ)",
        )
    ]

    supplier = deduplicate_suppliers(listings, product_keyword="handheld fan")[0]

    assert "Product title may not match sourcing intent." in supplier.risk_flags
    assert supplier.recommendation_tier == "D"
    assert supplier.recommended_action == "Do not shortlist until product match is verified"


def test_deduplicate_suppliers_downgrades_raw_material_results_for_finished_goods_sourcing():
    listings = [
        RawListing(
            platform="Made-in-China",
            source_url="https://www.made-in-china.com/search",
            product_url="https://supplier.example/product.html",
            supplier_url="https://supplier.en.made-in-china.com/",
            raw_product_name="Cosmetic Raw Material SLES Surfactant Chemical for Shampoo",
            raw_company_name="Raw Chemical Supplier",
            raw_price="US$1.20",
            raw_moq="25 kg",
        )
    ]

    supplier = deduplicate_suppliers(listings, product_keyword="private label personal care products")[0]

    assert "Listing appears to be raw material rather than a finished product." in supplier.risk_flags
    assert supplier.recommendation_tier == "D"
    assert supplier.recommended_action == "Do not shortlist raw material listings for finished-product sourcing"
    assert supplier.supplier_score < 40


def test_deduplicate_suppliers_flags_abnormally_low_price_against_market_median():
    listings = [
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/1.html",
            raw_supplier_id="normal-1",
            raw_product_name="Rechargeable Handheld Fan",
            raw_supplier_type="factory",
            raw_price="¥10.00",
            raw_moq="50 pieces",
        ),
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/2.html",
            raw_supplier_id="normal-2",
            raw_product_name="Rechargeable Handheld Fan",
            raw_supplier_type="factory",
            raw_price="¥11.00",
            raw_moq="50 pieces",
        ),
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/3.html",
            raw_supplier_id="suspicious-low",
            raw_product_name="Rechargeable Handheld Fan",
            raw_supplier_type="factory",
            raw_price="¥2.00",
            raw_moq="50 pieces",
        ),
    ]

    suppliers = deduplicate_suppliers(listings, product_keyword="handheld fan")
    suspicious = next(supplier for supplier in suppliers if supplier.products[0].supplier_id == "suspicious-low")

    assert "Price is far below market median; verify quotation." in suspicious.risk_flags
    assert suspicious.recommendation_tier != "A"


def test_deduplicate_suppliers_assigns_a_tier_to_strong_verified_factory():
    listings = [
        RawListing(
            platform="1688",
            source_url="https://openapi.elim.asia/v1/products/search",
            product_url="https://detail.1688.com/offer/100.html",
            raw_supplier_id="factory-100",
            raw_product_name="Portable Rechargeable Handheld Fan",
            raw_supplier_type="factory",
            raw_price="¥9.80",
            raw_moq="20 pieces",
        )
    ]

    supplier = deduplicate_suppliers(
        listings,
        product_keyword="handheld fan",
        target_price=12.0,
        moq_preference=50,
        supplier_preference="Factory Only",
    )[0]

    assert supplier.recommendation_tier == "A"
    assert supplier.risk_flags == []
    assert supplier.recommended_action == "Request quotation immediately"
