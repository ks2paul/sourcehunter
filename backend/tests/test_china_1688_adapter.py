import pytest
from playwright.async_api import async_playwright

from app.scraping.platforms.china_1688 import China1688Adapter, PlatformAccessBlocked, build_search_url


def test_build_search_url_uses_encoded_1688_keyword():
    assert build_search_url("手持风扇").startswith("https://s.1688.com/selloffer/offer_search.htm?keywords=")
    assert "%E6%89%8B%E6%8C%81%E9%A3%8E%E6%89%87" in build_search_url("手持风扇")


def test_raise_if_blocked_detects_1688_punish_url():
    with pytest.raises(PlatformAccessBlocked):
        China1688Adapter().raise_if_blocked("https://s.1688.com/selloffer/offer_search.htm/_____tmd_____/punish", "")


@pytest.mark.anyio
async def test_extract_listings_from_search_page_uses_only_visible_1688_data():
    html = """
    <section>
      <div class="offer-card">
        <a href="https://detail.1688.com/offer/123.html" title="手持小风扇 USB充电">手持小风扇 USB充电</a>
        <div class="price">¥12.50</div>
        <div class="moq">2件起批</div>
        <a href="https://shop123.1688.com/" title="深圳市真实电器有限公司">深圳市真实电器有限公司</a>
      </div>
      <div class="offer-card">
        <a href="javascript:;" title="Broken">Broken</a>
      </div>
    </section>
    """

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)

        listings = await China1688Adapter().extract_listings_from_page(
            page=page,
            source_url="https://s.1688.com/selloffer/offer_search.htm?keywords=%E6%89%8B%E6%8C%81%E9%A3%8E%E6%89%87",
            limit=5,
        )

        await browser.close()

    assert len(listings) == 1
    listing = listings[0]
    assert listing.platform == "1688"
    assert listing.product_url == "https://detail.1688.com/offer/123.html"
    assert listing.supplier_url == "https://shop123.1688.com/"
    assert listing.raw_product_name == "手持小风扇 USB充电"
    assert listing.raw_company_name == "深圳市真实电器有限公司"
    assert listing.raw_price == "¥12.50"
    assert listing.raw_moq == "2件起批"
