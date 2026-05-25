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
}


def expand_keywords(product_keyword: str) -> KeywordExpansion:
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
