from urllib.parse import urlparse

from playwright.async_api import Page

from app.scraping.browser import browser_page
from app.scraping.models import RawListing

PLATFORM = "Made-in-China"


def build_search_url(keyword: str) -> str:
    normalized = "_".join(part.capitalize() for part in keyword.strip().split() if part.strip())
    return f"https://www.made-in-china.com/products-search/hot-china-products/{normalized}.html"


class MadeInChinaAdapter:
    platform = PLATFORM

    async def search(self, keyword: str) -> list[RawListing]:
        source_url = build_search_url(keyword)
        async with browser_page() as page:
            await page.goto(source_url, wait_until="domcontentloaded", timeout=45_000)
            await page.locator(".prod-list .list-img").first.wait_for(timeout=20_000)
            return await self.extract_listings_from_page(page=page, source_url=source_url, limit=20)

    async def extract_listings_from_page(self, page: Page, source_url: str, limit: int = 20) -> list[RawListing]:
        cards = await page.locator(".prod-list .list-img").evaluate_all(
            """
            cards => cards.map(card => {
              const anchors = Array.from(card.querySelectorAll('a[href]'));
              const productAnchor = anchors.find(anchor => {
                const href = anchor.href || '';
                const text = (anchor.innerText || anchor.title || '').trim();
                const className = anchor.className || '';
                const looksLikePager = /^\\d+\\s*\\/\\s*\\d+$/.test(text);
                const looksLikeImageLink = className.includes('img-wrap') || className.includes('has-page');
                return text && !looksLikePager && !looksLikeImageLink && href.includes('/product/') && href.startsWith('http');
              });
              const supplierAnchor = anchors.find(anchor => {
                const href = anchor.href || '';
                const text = (anchor.innerText || '').trim();
                const className = anchor.className || '';
                return text && href.startsWith('http') && (
                  className.includes('compnay-name') ||
                  /\\.en\\.made-in-china\\.com\\/$/.test(href)
                );
              });
              const text = (card.innerText || '').split('\\n').map(line => line.trim()).filter(Boolean);
              const price = text.find(line => /^US\\$/i.test(line)) || null;
              const moq = text.find(line => /\\(MOQ\\)/i.test(line)) || null;
              return {
                product_name: productAnchor ? (productAnchor.innerText || productAnchor.title || '').trim() : null,
                product_url: productAnchor ? productAnchor.href : null,
                company_name: supplierAnchor ? (supplierAnchor.innerText || '').trim() : null,
                supplier_url: supplierAnchor ? supplierAnchor.href : null,
                price,
                moq,
              };
            })
            """
        )

        listings: list[RawListing] = []
        for card in cards:
            product_url = _clean_http_url(card.get("product_url"))
            supplier_url = _clean_http_url(card.get("supplier_url"))
            product_name = _clean_text(card.get("product_name"))
            company_name = _clean_text(card.get("company_name"))

            if not product_url or not supplier_url or not product_name or not company_name:
                continue

            listings.append(
                RawListing(
                    platform=self.platform,
                    source_url=source_url,
                    product_url=product_url,
                    supplier_url=supplier_url,
                    raw_product_name=product_name,
                    raw_company_name=company_name,
                    raw_price=_clean_text(card.get("price")),
                    raw_moq=_clean_text(card.get("moq")),
                )
            )
            if len(listings) >= limit:
                break

        return listings


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _clean_http_url(value: object) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return cleaned
