import json
import re

import httpx

from app.config import Settings, get_settings
from app.keyword_expansion import deterministic_expand_keywords
from app.models import PlatformSearchTerms, SourcingIntent
from app.sourcing_intent import (
    china_1688_finished_product_keyword,
    made_in_china_feature_terms,
    made_in_china_finished_product_keyword,
)


FEATURE_SPLIT_RE = re.compile(r"[,;/，、\s]+")


async def analyze_sourcing_intent(
    product_keyword: str,
    product_features: str | None = None,
    supplier_preference: str | None = None,
    settings: Settings | None = None,
) -> SourcingIntent:
    settings = settings or get_settings()
    if settings.ai_keyword_expansion_enabled and settings.openai_api_key:
        try:
            return await OpenAICompatibleSourcingIntentAnalyzer(settings=settings).analyze(
                product_keyword=product_keyword,
                product_features=product_features,
                supplier_preference=supplier_preference,
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return deterministic_analyze_sourcing_intent(
                product_keyword=product_keyword,
                product_features=product_features,
                supplier_preference=supplier_preference,
            )

    return deterministic_analyze_sourcing_intent(
        product_keyword=product_keyword,
        product_features=product_features,
        supplier_preference=supplier_preference,
    )


def deterministic_analyze_sourcing_intent(
    product_keyword: str,
    product_features: str | None = None,
    supplier_preference: str | None = None,
) -> SourcingIntent:
    normalized_keyword = product_keyword.strip()
    core_features = _feature_tokens(product_features)
    keyword_expansion = deterministic_expand_keywords(normalized_keyword)
    made_in_china_keyword = made_in_china_finished_product_keyword(normalized_keyword, keyword_expansion.english_keywords)
    china_1688_keyword = china_1688_finished_product_keyword(
        normalized_keyword,
        keyword_expansion.chinese_keywords or [normalized_keyword],
        supplier_preference,
    )

    if core_features:
        made_in_china_features = made_in_china_feature_terms(product_features)
        if made_in_china_features:
            made_in_china_keyword = _append_missing_terms(made_in_china_keyword, made_in_china_features.split())
        china_1688_keyword = _append_missing_terms(china_1688_keyword, core_features)

    excluded_categories = _excluded_categories_for(normalized_keyword)

    return SourcingIntent(
        normalized_product_keyword=normalized_keyword,
        product_summary=_summary_for(normalized_keyword, core_features),
        core_features=core_features,
        supporting_features=[],
        excluded_categories=excluded_categories,
        platform_search_terms=PlatformSearchTerms(
            made_in_china=made_in_china_keyword,
            china_1688=china_1688_keyword,
        ),
        confidence=0.74 if normalized_keyword else 0.35,
        source="deterministic_v1",
    )


class OpenAICompatibleSourcingIntentAnalyzer:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.client = client

    async def analyze(
        self,
        product_keyword: str,
        product_features: str | None = None,
        supplier_preference: str | None = None,
    ) -> SourcingIntent:
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
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a procurement intent analyst for a supplier discovery system. "
                                "Analyze the buyer's request before search. The product keyword is the anchor "
                                "and optional features can refine the product, but must not replace the main product. "
                                "Prioritize finished goods suppliers and real manufacturer search terms. "
                                "Generate platform-specific search terms for Made-in-China in English and 1688 in Chinese. "
                                "If a feature can cause wrong-category search, rewrite it safely. For example, translate "
                                "car-powered or 可车充 as 12v dc power, not car tools. "
                                "If the product keyword is Chinese, write product_summary, features, and excluded categories "
                                "in Chinese where possible. If the product keyword is English, use English. "
                                "Return only JSON with normalized_product_keyword, product_summary, core_features, "
                                "supporting_features, excluded_categories, platform_search_terms {made_in_china, china_1688}, "
                                "and confidence. Do not invent suppliers, prices, contacts, URLs, or company names."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Product keyword: {product_keyword.strip()}\n"
                                f"Optional product features: {(product_features or '').strip()}\n"
                                f"Supplier preference: {supplier_preference or 'Factory Preferred'}"
                            ),
                        },
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            payload = json.loads(content)
            return _intent_from_payload(
                payload=payload,
                product_keyword=product_keyword,
                product_features=product_features,
                supplier_preference=supplier_preference,
            )
        finally:
            if close_client:
                await client.aclose()


def _intent_from_payload(
    payload: dict,
    product_keyword: str,
    product_features: str | None,
    supplier_preference: str | None,
) -> SourcingIntent:
    fallback = deterministic_analyze_sourcing_intent(product_keyword, product_features, supplier_preference)
    platform_terms = payload.get("platform_search_terms")
    if not isinstance(platform_terms, dict):
        platform_terms = {}

    made_in_china = _clean_text(platform_terms.get("made_in_china")) or fallback.platform_search_terms.made_in_china
    china_1688 = _clean_text(platform_terms.get("china_1688")) or fallback.platform_search_terms.china_1688
    ai_excluded_categories = _clean_list(payload.get("excluded_categories"))
    excluded_categories = _merge_unique(ai_excluded_categories, fallback.excluded_categories)

    return SourcingIntent(
        normalized_product_keyword=_clean_text(payload.get("normalized_product_keyword")) or fallback.normalized_product_keyword,
        product_summary=_clean_text(payload.get("product_summary")) or fallback.product_summary,
        core_features=_clean_list(payload.get("core_features")) or fallback.core_features,
        supporting_features=_clean_list(payload.get("supporting_features")),
        excluded_categories=excluded_categories,
        platform_search_terms=PlatformSearchTerms(
            made_in_china=made_in_china,
            china_1688=china_1688,
        ),
        confidence=_confidence_value(payload.get("confidence"), fallback.confidence),
        source="openai_compatible",
    )


def _feature_tokens(product_features: str | None) -> list[str]:
    if not product_features:
        return []
    return [token.strip() for token in FEATURE_SPLIT_RE.split(product_features) if token.strip()][:10]


def _append_missing_terms(keyword: str, terms: list[str]) -> str:
    result = keyword.strip()
    normalized = result.lower()
    for term in terms:
        clean = term.strip()
        if clean and clean.lower() not in normalized:
            result = f"{result} {clean}"
            normalized = result.lower()
    return result


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*primary, *secondary]:
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            merged.append(item)
            seen.add(normalized)
    return merged[:12]


def _excluded_categories_for(product_keyword: str) -> list[str]:
    normalized = product_keyword.lower()
    compact = re.sub(r"\s+", "", normalized)
    if "充气泵" in compact and any(term in compact for term in ("床垫", "充气床", "气垫床")):
        return ["成人用品", "轮胎充气泵", "汽车维修工具", "大型工业泵", "空压机"]
    if "phone case" in normalized or "手机壳" in compact or "保护壳" in compact:
        return ["手机壳生产设备", "手机壳模具", "打印机", "非指定机型配件"]
    return ["raw materials", "unrelated accessories", "tooling or production equipment"]


def _summary_for(product_keyword: str, core_features: list[str]) -> str:
    if core_features:
        return f"Find finished-goods suppliers for {product_keyword}, using {', '.join(core_features)} as refinement features."
    return f"Find finished-goods suppliers for {product_keyword}."


def _clean_text(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()][:12]


def _confidence_value(value: object, fallback: float) -> float:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"high", "strong"}:
            return 0.85
        if normalized in {"medium", "moderate"}:
            return 0.65
        if normalized in {"low", "weak"}:
            return 0.4
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback
