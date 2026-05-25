from urllib.parse import quote, urlparse

from playwright.async_api import Page

from app.scraping.browser import browser_page
from app.scraping.models import RawListing

PLATFORM = "1688"


class PlatformAccessBlocked(RuntimeError):
    pass


def build_search_url(keyword: str) -> str:
    return f"https://s.1688.com/selloffer/offer_search.htm?keywords={quote(keyword.strip())}"


class China1688Adapter:
    platform = PLATFORM

    async def search(self, keyword: str) -> list[RawListing]:
        source_url = build_search_url(keyword)
        async with browser_page() as page:
            await page.goto(source_url, wait_until="domcontentloaded", timeout=45_000)
            body_text = await page.locator("body").inner_text(timeout=10_000)
            self.raise_if_blocked(page.url, body_text)
            return await self.extract_listings_from_page(page=page, source_url=source_url, limit=20)

    def raise_if_blocked(self, current_url: str, body_text: str) -> None:
        normalized_body = body_text.lower()
        if "punish" in current_url or "_____tmd_____" in current_url or "x5sec" in current_url:
            raise PlatformAccessBlocked("1688 blocked automated access with an anti-bot challenge.")
        if "验证码" in body_text or "滑块" in body_text or "security check" in normalized_body:
            raise PlatformAccessBlocked("1688 requires human verification before listings can be retrieved.")

    async def extract_listings_from_page(self, page: Page, source_url: str, limit: int = 20) -> list[RawListing]:
        cards = await page.locator("body").evaluate(
            """
            body => {
              const productAnchors = Array.from(body.querySelectorAll('a[href*="detail.1688.com/offer/"]'));
              return productAnchors.map(productAnchor => {
                const card = productAnchor.closest('[class*="offer"], [class*="card"], [class*="item"], li, div') || productAnchor.parentElement;
                const anchors = Array.from((card || body).querySelectorAll('a[href]'));
                const supplierAnchor = anchors.find(anchor => {
                  const href = anchor.href || '';
                  return href.startsWith('http') && href.includes('1688.com') && !href.includes('detail.1688.com/offer/');
                });
                const text = ((card || productAnchor).innerText || '').split('\\n').map(line => line.trim()).filter(Boolean);
                const price = text.find(line => /^[¥￥]/.test(line)) || null;
                const moq = text.find(line => /起批|MOQ/i.test(line)) || null;
                return {
                  product_name: (productAnchor.innerText || productAnchor.title || '').trim(),
                  product_url: productAnchor.href,
                  company_name: supplierAnchor ? (supplierAnchor.innerText || supplierAnchor.title || '').trim() : null,
                  supplier_url: supplierAnchor ? supplierAnchor.href : null,
                  price,
                  moq,
                };
              });
            }
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
