from urllib.parse import urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

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
            await self._wait_for_listing_candidates(page)
            return await self.extract_listings_from_page(page=page, source_url=source_url, limit=20)

    async def extract_listings_from_page(self, page: Page, source_url: str, limit: int = 20) -> list[RawListing]:
        cards = await page.locator("body").evaluate(
            """
            body => {
              const root = body.querySelector('.prod-list') || body;
              const seen = new Set();
              const productAnchors = Array.from(root.querySelectorAll('a[href]')).filter(anchor => {
                const href = anchor.href || '';
                const text = (anchor.innerText || anchor.title || '').trim();
                const className = anchor.className || '';
                const looksLikePager = /^\\d+\\s*\\/\\s*\\d+$/.test(text);
                return !looksLikePager && href.startsWith('http') && href.includes('.en.made-in-china.com/product/');
              });

              return productAnchors.map(productAnchor => {
                const href = productAnchor.href || '';
                if (seen.has(href)) {
                  return null;
                }
                seen.add(href);

                const card =
                  productAnchor.closest('.list-img') ||
                  productAnchor.closest('.product-item, [class*="product-item"], [class*="prod-item"], article, li') ||
                  productAnchor.parentElement ||
                  body;
                const anchors = Array.from(card.querySelectorAll('a[href]'));
                const productImage = productAnchor.querySelector('img[alt]');
                const anchorText = (productAnchor.innerText || '').trim();
                const anchorTitle = (productAnchor.title || '').trim();
                const imageAlt = productImage ? (productImage.alt || '').trim() : '';
                const productName = (
                  anchorText ||
                  anchorTitle ||
                  imageAlt ||
                  ''
                ).trim();

                let supplierOrigin = null;
                try {
                  supplierOrigin = new URL(href).origin + '/';
                } catch {
                  supplierOrigin = null;
                }

                const supplierAnchor = anchors.find(anchor => {
                  const anchorHref = anchor.href || '';
                  const text = (anchor.innerText || '').trim();
                  const className = anchor.className || '';
                  return text && anchorHref.startsWith('http') && (
                    className.includes('compnay-name') ||
                    className.includes('company-name') ||
                    anchorHref === supplierOrigin
                  );
                });

                const cardText = (card.innerText || '').replace(/\\s+/g, ' ').trim();
                const text = cardText.split('\\n').map(line => line.trim()).filter(Boolean);
                const priceMatch = cardText.match(/US\\$\\s*[\\d,.]+(?:\\s*-\\s*[\\d,.]+)?/i);
                const moqMatch = cardText.match(/[\\d,]+\\s+[^\\s]+\\s+\\(MOQ\\)/i);
                const price = text.find(line => /^US\\$/i.test(line)) || null;
                const moq = text.find(line => /\\(MOQ\\)/i.test(line)) || null;
                return {
                  product_name: productName || null,
                  product_url: href,
                  company_name: supplierAnchor ? (supplierAnchor.innerText || '').trim() : null,
                  supplier_url: supplierAnchor ? supplierAnchor.href : supplierOrigin,
                  price: priceMatch ? priceMatch[0].replace(/\\s+/g, '') : price,
                  moq: moqMatch ? moqMatch[0] : moq,
                };
              }).filter(Boolean);
            }
            """
        )

        if not cards:
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

            if not product_url or not supplier_url or not product_name:
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

    async def _wait_for_listing_candidates(self, page: Page) -> None:
        for selector in (
            'a[href*=".en.made-in-china.com/product/"]',
            ".prod-list .list-img",
            ".product-item",
            '[class*="product-item"]',
        ):
            try:
                await page.locator(selector).first.wait_for(state="attached", timeout=8_000)
                return
            except PlaywrightTimeoutError:
                continue


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
