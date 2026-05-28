import httpx
import pytest

from app.config import Settings
from app.sourcing_analysis import (
    OpenAICompatibleSourcingIntentAnalyzer,
    analyze_sourcing_intent,
    deterministic_analyze_sourcing_intent,
)


def test_deterministic_intent_keeps_product_keyword_as_anchor_and_features_as_refinement():
    intent = deterministic_analyze_sourcing_intent(
        product_keyword="床垫充气泵",
        product_features="可移动，可车充，充电款",
        supplier_preference="Factory Preferred",
    )

    assert intent.normalized_product_keyword == "床垫充气泵"
    assert "可移动" in intent.core_features
    assert "成人用品" in intent.excluded_categories
    assert "12v dc" in intent.platform_search_terms.made_in_china
    assert "car adapter" not in intent.platform_search_terms.made_in_china
    assert "充气床" in intent.platform_search_terms.china_1688
    assert "可车充" in intent.platform_search_terms.china_1688


@pytest.mark.anyio
async def test_openai_compatible_sourcing_intent_analyzer_parses_structured_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.example.test/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                              "normalized_product_keyword": "portable mattress air pump",
                              "product_summary": "Find portable mattress air pump factories.",
                              "core_features": ["rechargeable", "12v dc"],
                              "supporting_features": ["compact"],
                              "excluded_categories": ["tire inflator", "adult products"],
                              "platform_search_terms": {
                                "made_in_china": "portable electric air pump for inflatable mattress rechargeable 12v dc manufacturer",
                                "china_1688": "充气床 电动充气泵 便携 充电 小型 厂家 工厂"
                              },
                              "confidence": "high"
                            }
                            """
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        analyzer = OpenAICompatibleSourcingIntentAnalyzer(
            settings=Settings(
                _env_file=None,
                openai_api_key="test-key",
                openai_base_url="https://api.example.test/v1",
                openai_model="test-model",
            ),
            client=client,
        )
        intent = await analyzer.analyze("床垫充气泵", "可移动，可车充，充电款")

    assert intent.source == "openai_compatible"
    assert intent.normalized_product_keyword == "portable mattress air pump"
    assert intent.core_features == ["rechargeable", "12v dc"]
    assert "adult products" in intent.excluded_categories
    assert "成人用品" in intent.excluded_categories
    assert intent.platform_search_terms.china_1688 == "充气床 电动充气泵 便携 充电 小型 厂家 工厂"
    assert intent.confidence == 0.85


@pytest.mark.anyio
async def test_analyze_sourcing_intent_falls_back_when_openai_key_is_missing():
    settings = Settings(_env_file=None, openai_api_key=None)

    intent = await analyze_sourcing_intent("handheld fan", "rechargeable", settings=settings)

    assert intent.source == "deterministic_v1"
    assert intent.normalized_product_keyword == "handheld fan"
    assert "rechargeable" in intent.core_features
