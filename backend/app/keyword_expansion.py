import json

import httpx

from app.config import Settings, get_settings
from app.models import KeywordExpansion

KNOWN_EXPANSIONS = {
    "handheld fan": KeywordExpansion(
        english_keywords=[
            "handheld fan",
            "mini fan",
            "portable fan",
            "rechargeable fan",
            "cooling fan",
        ],
        chinese_keywords=[
            "手持风扇",
            "便携风扇",
            "充电风扇",
            "小风扇",
            "折叠风扇",
        ],
        variation_keywords=["usb fan", "desk fan", "travel fan"],
        confidence=0.86,
        source="deterministic_v1",
    ),
    "pet wipes": KeywordExpansion(
        english_keywords=[
            "pet wipes",
            "dog wipes",
            "cat wipes",
            "pet cleaning wipes",
            "deodorizing pet wipes",
        ],
        chinese_keywords=[
            "宠物湿巾",
            "狗狗湿巾",
            "猫咪湿巾",
            "宠物清洁湿巾",
            "除臭宠物湿巾",
        ],
        variation_keywords=["unscented pet wipes", "biodegradable pet wipes"],
        confidence=0.84,
        source="deterministic_v1",
    ),
    "picture frame": KeywordExpansion(
        english_keywords=[
            "picture frame",
            "photo frame",
            "wall frame",
            "tabletop frame",
            "wood picture frame",
        ],
        chinese_keywords=[
            "相框",
            "照片框",
            "画框",
            "木质相框",
            "桌面相框",
        ],
        variation_keywords=["gallery frame", "poster frame", "certificate frame"],
        confidence=0.88,
        source="deterministic_v1",
    ),
    "台式咖啡机": KeywordExpansion(
        english_keywords=[
            "home coffee machine",
            "coffee maker",
            "espresso machine",
            "tabletop coffee maker",
            "automatic coffee maker",
        ],
        chinese_keywords=[
            "台式咖啡机",
            "桌面咖啡机",
            "意式咖啡机",
            "家用咖啡机",
            "自动咖啡机",
        ],
        variation_keywords=["semi automatic espresso machine", "bean to cup coffee machine", "capsule coffee machine"],
        confidence=0.82,
        source="deterministic_v1",
    ),
}


def deterministic_expand_keywords(product_keyword: str) -> KeywordExpansion:
    normalized = product_keyword.strip().lower()
    if normalized in KNOWN_EXPANSIONS:
        return KNOWN_EXPANSIONS[normalized]

    return KeywordExpansion(
        english_keywords=[product_keyword.strip()],
        chinese_keywords=[],
        variation_keywords=[],
        confidence=0.35,
        source="deterministic_v1",
    )


class OpenAICompatibleKeywordExpander:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.client = client

    async def expand(self, product_keyword: str) -> KeywordExpansion:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30)
        try:
            response = await client.post(
                f"{self.settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.openai_model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You expand product sourcing terminology for procurement. "
                                "Return only JSON with english_keywords, chinese_keywords, "
                                "variation_keywords, and confidence. Do not invent suppliers, "
                                "prices, contacts, URLs, or company names."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Product keyword: {product_keyword.strip()}",
                        },
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            payload = json.loads(content)
            return KeywordExpansion(
                english_keywords=_clean_keyword_list(payload.get("english_keywords"), product_keyword),
                chinese_keywords=_clean_keyword_list(payload.get("chinese_keywords"), None),
                variation_keywords=_clean_keyword_list(payload.get("variation_keywords"), None),
                confidence=float(payload.get("confidence", 0.7)),
                source="openai_compatible",
            )
        finally:
            if close_client:
                await client.aclose()


def _clean_keyword_list(value: object, fallback: str | None) -> list[str]:
    if not isinstance(value, list):
        return [fallback] if fallback else []
    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if not cleaned and fallback:
        return [fallback]
    return cleaned[:10]


async def expand_keywords(product_keyword: str, settings: Settings | None = None) -> KeywordExpansion:
    settings = settings or get_settings()
    if settings.ai_keyword_expansion_enabled and settings.openai_api_key:
        try:
            return await OpenAICompatibleKeywordExpander(settings=settings).expand(product_keyword)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return deterministic_expand_keywords(product_keyword)

    return deterministic_expand_keywords(product_keyword)
