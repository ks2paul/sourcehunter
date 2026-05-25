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
