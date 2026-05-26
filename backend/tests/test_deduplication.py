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
