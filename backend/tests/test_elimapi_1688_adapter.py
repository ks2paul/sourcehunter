import json

import httpx
import pytest

from app.deduplication import deduplicate_suppliers
from app.scraping.platforms.elimapi_1688 import Elimapi1688Adapter, ElimapiNotConfigured


@pytest.mark.anyio
async def test_elimapi_1688_search_posts_keyword_and_api_key():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["x-api-key"] == "test-key"
        if request.url.path == "/v1/products/search":
            assert request.method == "POST"
            assert json.loads(request.content) == {
                "q": "手持风扇",
                "platform": "alibaba",
                "lang": "en",
                "page": 1,
                "size": 10,
            }
            return httpx.Response(
                201,
                json={
                    "items": [
                        {
                            "id": "123",
                            "title": "手持小风扇",
                            "titleEn": "Rechargeable handheld fan",
                            "price": "12.50",
                            "moq": 2,
                            "link": "https://detail.1688.com/offer/123.html",
                        }
                    ]
                },
            )
        assert request.url.path == "/v1/products/detail"
        assert json.loads(request.content) == {"id": "123", "platform": "alibaba", "lang": "en"}
        return httpx.Response(
            201,
            json={
                "shop_id": "shop-123",
                "shop_name": "深圳市真实电器有限公司",
                "seller_type": "factory",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        listings = await Elimapi1688Adapter(api_key="test-key", client=client).search("手持风扇")

    assert len(listings) == 1
    listing = listings[0]
    assert listing.platform == "1688"
    assert listing.source_url == "https://openapi.elim.asia/v1/products/search"
    assert listing.product_url == "https://detail.1688.com/offer/123.html"
    assert listing.supplier_url is None
    assert listing.raw_supplier_id == "shop-123"
    assert listing.raw_product_name == "Rechargeable handheld fan"
    assert listing.raw_company_name == "深圳市真实电器有限公司"
    assert listing.raw_price == "¥12.50"
    assert listing.raw_moq == "2 Pieces (MOQ)"
    assert listing.raw_supplier_type == "factory"
    assert [request.url.path for request in requests] == ["/v1/products/search", "/v1/products/detail"]


@pytest.mark.anyio
async def test_elimapi_1688_requires_api_key():
    with pytest.raises(ElimapiNotConfigured):
        await Elimapi1688Adapter(api_key="").search("手持风扇")


def test_elimapi_verified_factory_allows_factory_only():
    listing = Elimapi1688Adapter.build_listing(
        {
            "id": "123",
            "title": "手持小风扇",
            "price": "12.50",
            "moq": 2,
            "seller": {
                "name": "深圳市真实电器有限公司",
                "url": "https://shop123.1688.com/",
                "seller_type": "factory",
            },
            "url": "https://detail.1688.com/offer/123.html",
        }
    )

    suppliers = deduplicate_suppliers([listing], product_keyword="手持风扇", supplier_preference="Factory Only")

    assert len(suppliers) == 1
    assert suppliers[0].supplier_type == "Verified Factory"


def test_elimapi_1688_uses_nested_chinese_shop_name_when_english_name_is_missing():
    listing = Elimapi1688Adapter.build_listing(
        {
            "data": {
                "offer": {
                    "id": "456",
                    "title": "洗发水沐浴露套装",
                    "url": "https://detail.1688.com/offer/456.html",
                },
                "shopInfo": {
                    "shopId": "shop-456",
                    "shopName": "广州真实日化用品有限公司",
                    "shopUrl": "https://shop456.1688.com/",
                    "sellerType": "factory",
                },
            }
        }
    )

    assert listing is not None
    assert listing.raw_company_name == "广州真实日化用品有限公司"
    assert listing.raw_supplier_id == "shop-456"
    assert listing.supplier_url == "https://shop456.1688.com/"
    assert listing.raw_supplier_type == "factory"


def test_elimapi_1688_does_not_use_product_title_as_company_name():
    listing = Elimapi1688Adapter.build_listing(
        {
            "id": "789",
            "title": "洗发水沐浴露套装",
            "url": "https://detail.1688.com/offer/789.html",
            "shop_id": "shop-789",
            "price": "8.80",
        }
    )

    assert listing is not None
    assert listing.raw_product_name == "洗发水沐浴露套装"
    assert listing.raw_company_name is None
