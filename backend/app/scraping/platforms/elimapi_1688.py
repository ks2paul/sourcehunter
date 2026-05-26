from typing import Any

import httpx

from app.config import get_settings
from app.scraping.models import RawListing

PLATFORM = "1688"
SEARCH_PATH = "/products/search"
DETAIL_PATH = "/products/detail"


class ElimapiNotConfigured(RuntimeError):
    pass


class ElimapiRequestFailed(RuntimeError):
    pass


class Elimapi1688Adapter:
    platform = PLATFORM

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.elimapi_api_key
        self.base_url = (base_url or settings.elimapi_base_url).rstrip("/")
        self.client = client

    async def search(self, keyword: str) -> list[RawListing]:
        if not self.api_key:
            raise ElimapiNotConfigured("Elimapi API key is not configured.")

        payload = {"q": keyword, "platform": "alibaba", "lang": "en", "page": 1, "size": 10}
        if self.client is not None:
            response = await self._post(self.client, payload)
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await self._post(client, payload)

        if response.status_code >= 400:
            raise ElimapiRequestFailed(f"Elimapi search failed with status {response.status_code}.")

        listings: list[RawListing] = []
        for item in _extract_items(response.json()):
            detail = await self._fetch_detail(item)
            merged_item = _merge_without_empty_overrides(item, detail)
            listing = self.build_listing(merged_item, source_url=f"{self.base_url}{SEARCH_PATH}")
            if listing is not None:
                listings.append(listing)
        return listings[:10]

    async def _post(self, client: httpx.AsyncClient, payload: dict[str, Any]) -> httpx.Response:
        return await client.post(
            f"{self.base_url}{SEARCH_PATH}",
            headers={"x-api-key": self.api_key or "", "Content-Type": "application/json"},
            json=payload,
        )

    async def _fetch_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        product_id = _string_value(item, "id", "offerId", "offer_id", "productId", "product_id")
        if not product_id:
            return {}

        payload = {"id": product_id, "platform": "alibaba", "lang": "en"}
        if self.client is not None:
            response = await self.client.post(
                f"{self.base_url}{DETAIL_PATH}",
                headers={"x-api-key": self.api_key or "", "Content-Type": "application/json"},
                json=payload,
            )
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}{DETAIL_PATH}",
                    headers={"x-api-key": self.api_key or "", "Content-Type": "application/json"},
                    json=payload,
                )
        if response.status_code >= 400:
            return {}
        detail = response.json()
        return detail if isinstance(detail, dict) else {}

    @staticmethod
    def build_listing(item: dict[str, Any], source_url: str = "https://openapi.elim.asia/v1/products/search") -> RawListing | None:
        product_id = _string_value(item, "id", "offerId", "offer_id", "productId", "product_id")
        product_url = _string_value(item, "url", "link", "productUrl", "product_url", "detailUrl", "detail_url")
        if product_url is None and product_id:
            product_url = f"https://detail.1688.com/offer/{product_id}.html"

        seller = _dict_value(item, "seller", "shop", "supplier") or {}
        supplier_url = _string_value(item, "sellerUrl", "seller_url", "shopUrl", "shop_url")
        supplier_url = supplier_url or _string_value(seller, "url", "shopUrl", "shop_url", "sellerUrl", "seller_url")
        supplier_id = _string_value(item, "shop_id", "shopId", "seller_id", "sellerId", "supplier_id", "supplierId")
        supplier_id = supplier_id or _string_value(seller, "id", "shop_id", "shopId", "seller_id", "sellerId")

        product_name = _string_value(item, "titleEn", "title_en", "nameEn", "name_en")
        product_name = product_name or _string_value(item, "title", "name", "subject")
        company_name = _string_value(item, "sellerName", "seller_name", "shopName", "shop_name", "companyName", "company_name")
        company_name = company_name or _string_value(seller, "name", "title", "companyName", "company_name")

        if not product_url or not product_name or not (supplier_url or supplier_id or company_name):
            return None

        return RawListing(
            platform=PLATFORM,
            source_url=source_url,
            product_url=product_url,
            supplier_url=supplier_url,
            raw_supplier_id=supplier_id,
            raw_product_name=product_name,
            raw_company_name=company_name,
            raw_price=_format_price(_first_value(item, "promotion_price", "promotionPrice", "price", "retail_price", "dropship_price")),
            raw_moq=_format_moq(_first_value(item, "moq", "minOrderQuantity", "min_order_quantity", "minimumOrderQuantity")),
            raw_supplier_type=_string_value(item, "seller_type", "sellerType") or _string_value(seller, "seller_type", "sellerType"),
        )


def _extract_items(data: Any) -> list[dict[str, Any]]:
    candidates = [
        data,
        data.get("data") if isinstance(data, dict) else None,
        data.get("result") if isinstance(data, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            for key in ("items", "products", "list", "results", "data"):
                value = candidate.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
    return []


def _merge_without_empty_overrides(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if value not in (None, ""):
            merged[key] = value
    return merged


def _first_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _string_value(data: dict[str, Any], *keys: str) -> str | None:
    value = _first_value(data, *keys)
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _dict_value(data: dict[str, Any], *keys: str) -> dict[str, Any] | None:
    value = _first_value(data, *keys)
    return value if isinstance(value, dict) else None


def _format_price(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = _first_value(value, "min", "value", "price")
    cleaned = " ".join(str(value).split())
    if not cleaned:
        return None
    return cleaned if cleaned.startswith(("¥", "￥", "CNY")) else f"¥{cleaned}"


def _format_moq(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = _first_value(value, "min", "value", "quantity")
    cleaned = " ".join(str(value).split())
    if not cleaned:
        return None
    return cleaned if "MOQ" in cleaned or "起批" in cleaned else f"{cleaned} Pieces (MOQ)"
