import pytest
from playwright.async_api import async_playwright

from app.scraping.platforms.made_in_china import MadeInChinaAdapter, build_search_url


def test_build_search_url_uses_made_in_china_keyword_format():
    assert (
        build_search_url("handheld fan")
        == "https://www.made-in-china.com/products-search/hot-china-products/Handheld_Fan.html"
    )


@pytest.mark.anyio
async def test_extract_listings_from_search_page_uses_only_visible_source_data():
    html = """
    <section class="prod-list">
      <div class="list-img">
        <a class="has-page swiper-page-wrap" href="https://supplier-a.en.made-in-china.com/product/abc.html">1/ 6</a>
        <a title="Rechargeable Turbo Mini Fan" href="https://supplier-a.en.made-in-china.com/product/abc.html">
          Rechargeable Turbo Mini Fan
        </a>
        <div class="price">US$3.50-4.50</div>
        <div class="moq">1,000 Pieces (MOQ)</div>
        <a class="compnay-name" href="https://supplier-a.en.made-in-china.com/">Shenzhen Realmark Industrial Co., Ltd.</a>
      </div>
      <div class="list-img">
        <a title="Broken Listing" href="javascript:;">Broken Listing</a>
        <div class="price">Contact Now</div>
      </div>
    </section>
    """

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)

        listings = await MadeInChinaAdapter().extract_listings_from_page(
            page=page,
            source_url="https://www.made-in-china.com/products-search/hot-china-products/Handheld_Fan.html",
            limit=5,
        )

        await browser.close()

    assert len(listings) == 1
    listing = listings[0]
    assert listing.platform == "Made-in-China"
    assert listing.source_url == "https://www.made-in-china.com/products-search/hot-china-products/Handheld_Fan.html"
    assert listing.product_url == "https://supplier-a.en.made-in-china.com/product/abc.html"
    assert listing.supplier_url == "https://supplier-a.en.made-in-china.com/"
    assert listing.raw_product_name == "Rechargeable Turbo Mini Fan"
    assert listing.raw_company_name == "Shenzhen Realmark Industrial Co., Ltd."
    assert listing.raw_price == "US$3.50-4.50"
    assert listing.raw_moq == "1,000 Pieces (MOQ)"


@pytest.mark.anyio
async def test_extract_listings_from_search_page_handles_product_links_without_legacy_card_class():
    html = """
    <main>
      <article class="product-item">
        <a href="https://supplier-b.en.made-in-china.com/product/xyz.html">
          <img alt="Portable Rechargeable Handheld Fan" />
        </a>
        <span>US$2.20-3.00</span>
        <span>100 Pieces (MOQ)</span>
      </article>
    </main>
    """

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)

        listings = await MadeInChinaAdapter().extract_listings_from_page(
            page=page,
            source_url="https://www.made-in-china.com/products-search/hot-china-products/Handheld_Fan.html",
            limit=5,
        )

        await browser.close()

    assert len(listings) == 1
    listing = listings[0]
    assert listing.product_url == "https://supplier-b.en.made-in-china.com/product/xyz.html"
    assert listing.supplier_url == "https://supplier-b.en.made-in-china.com/"
    assert listing.raw_product_name == "Portable Rechargeable Handheld Fan"
    assert listing.raw_company_name is None
    assert listing.raw_price == "US$2.20-3.00"
    assert listing.raw_moq == "100 Pieces (MOQ)"
