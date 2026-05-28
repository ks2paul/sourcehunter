from __future__ import annotations

import re


BROAD_FINISHED_PRODUCT_KEYWORDS = {
    "日化洗护用品": {
        "made_in_china": "private label personal care products manufacturer",
        "china_1688": "洗护用品 成品 OEM",
        "english": [
            "private label personal care products",
            "shampoo manufacturer",
            "body wash manufacturer",
            "laundry detergent supplier",
            "hand wash manufacturer",
            "wet wipes manufacturer",
        ],
        "chinese": ["洗发水", "沐浴露", "洗衣液", "洗手液", "湿巾", "护发素"],
        "variation": [
            "personal care finished products",
            "OEM personal care products",
            "ODM washing products",
            "private label toiletries",
        ],
    },
    "洗护用品": {
        "made_in_china": "private label personal care products manufacturer",
        "china_1688": "洗护用品 成品 OEM",
        "english": [
            "private label personal care products",
            "shampoo manufacturer",
            "body wash manufacturer",
            "hand wash manufacturer",
        ],
        "chinese": ["洗发水", "沐浴露", "洗手液", "护发素"],
        "variation": ["personal care finished products", "OEM personal care products"],
    },
}

SPECIFIC_PRODUCT_INTENT_KEYWORDS = {
    "床垫充气泵": {
        "made_in_china": "portable mattress air pump rechargeable car adapter manufacturer",
        "china_1688": "床垫 便携 充气泵 车载 充电 小型",
    },
    "充气床垫泵": {
        "made_in_china": "portable mattress air pump rechargeable car adapter manufacturer",
        "china_1688": "充气床垫 便携 充气泵 车载 充电 小型",
    },
}

CHINESE_FEATURE_TO_ENGLISH = {
    "可移动": "portable",
    "便携": "portable",
    "小型": "compact",
    "小容量": "small capacity",
    "迷你": "mini",
    "可车充": "car adapter",
    "车充": "car adapter",
    "车载": "car adapter",
    "汽车": "car",
    "充电款": "rechargeable",
    "充电": "rechargeable",
    "无线": "cordless",
    "电池": "battery powered",
    "家用": "home use",
    "户外": "outdoor",
}

MADE_IN_CHINA_INTENT_TERMS = (
    "manufacturer",
    "supplier",
    "factory",
    "oem",
    "odm",
    "private label",
    "finished product",
)

RAW_MATERIAL_TERMS = (
    "raw material",
    "raw materials",
    "ingredient",
    "ingredients",
    "cosmetic ingredient",
    "active ingredient",
    "surfactant",
    "chemical",
    "chemicals",
    "sodium laureth sulfate",
    "sles",
    "labsa",
    "extract",
    "fragrance oil",
    "material for",
    "原料",
    "表面活性剂",
    "化工",
    "化学品",
    "月桂醇",
    "硫酸钠",
    "香精",
    "提取物",
)

FINISHED_GOODS_TERMS = (
    "finished product",
    "private label",
    "oem",
    "odm",
    "manufacturer",
    "supplier",
    "成品",
    "贴牌",
    "代工",
)


def broad_finished_product_expansion(product_keyword: str) -> dict[str, list[str] | str] | None:
    normalized = _normalize_key(product_keyword)
    return BROAD_FINISHED_PRODUCT_KEYWORDS.get(normalized)


def made_in_china_finished_product_keyword(product_keyword: str, english_keywords: list[str]) -> str:
    broad_expansion = broad_finished_product_expansion(product_keyword)
    if broad_expansion:
        return str(broad_expansion["made_in_china"])
    specific_expansion = specific_product_intent(product_keyword)
    if specific_expansion:
        return str(specific_expansion["made_in_china"])

    keyword = _first_keyword(english_keywords, product_keyword)
    if "咖啡机" in _normalize_key(product_keyword):
        keyword = "home coffee machine" if ("台式" in product_keyword or "桌面" in product_keyword) else "coffee maker"

    return _with_made_in_china_intent(keyword)


def china_1688_finished_product_keyword(
    product_keyword: str,
    chinese_keywords: list[str],
    supplier_preference: str | None = None,
) -> str:
    broad_expansion = broad_finished_product_expansion(product_keyword)
    if broad_expansion:
        keyword = str(broad_expansion["china_1688"])
    else:
        specific_expansion = specific_product_intent(product_keyword)
        keyword = str(specific_expansion["china_1688"]) if specific_expansion else _first_keyword(chinese_keywords, product_keyword)
    if supplier_preference in ("Factory Preferred", "Factory Only"):
        return _with_1688_factory_intent(keyword)
    return keyword


def looks_like_raw_material_result(product_name: str | None) -> bool:
    normalized = _normalize_text(product_name)
    if not normalized:
        return False
    has_raw_material_signal = any(term in normalized for term in RAW_MATERIAL_TERMS)
    has_finished_goods_signal = any(term in normalized for term in FINISHED_GOODS_TERMS)
    return has_raw_material_signal and not has_finished_goods_signal


def specific_product_intent(product_keyword: str) -> dict[str, str] | None:
    normalized = _normalize_key(product_keyword)
    return SPECIFIC_PRODUCT_INTENT_KEYWORDS.get(normalized)


def made_in_china_feature_terms(product_features: str | None) -> str:
    normalized = _normalize_text(product_features)
    if not normalized:
        return ""
    terms: list[str] = []
    compact = _normalize_key(product_features or "")
    for chinese_term, english_term in CHINESE_FEATURE_TO_ENGLISH.items():
        if chinese_term in compact and english_term not in terms:
            terms.append(english_term)

    raw_tokens = [token for token in re.split(r"[,;/，、\s]+", normalized) if token]
    english_tokens = [token for token in raw_tokens if re.search(r"[a-z0-9]", token)]
    for token in english_tokens:
        if token not in terms:
            terms.append(token)
    return " ".join(terms[:8])


def _with_made_in_china_intent(keyword: str) -> str:
    normalized = _normalize_text(keyword)
    if any(term in normalized for term in MADE_IN_CHINA_INTENT_TERMS):
        return keyword.strip()
    return f"{keyword.strip()} manufacturer"


def _with_1688_factory_intent(keyword: str) -> str:
    normalized = _normalize_text(keyword)
    factory_terms = ("厂家", "工厂", "源头厂家", "源头工厂", "生产厂家", "oem", "odm", "代工")
    if any(term in normalized for term in factory_terms):
        return keyword.strip()
    return f"{keyword.strip()} 厂家 工厂 源头厂家 OEM"


def _first_keyword(keywords: list[str], fallback: str) -> str:
    return next((keyword.strip() for keyword in keywords if keyword.strip()), fallback.strip())


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def _normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())
