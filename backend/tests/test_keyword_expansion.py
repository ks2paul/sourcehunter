import httpx
import pytest

from app.config import Settings
from app.keyword_expansion import OpenAICompatibleKeywordExpander, expand_keywords


@pytest.mark.anyio
async def test_openai_compatible_expander_parses_structured_response():
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
                              "english_keywords": ["solar garden light", "outdoor solar light"],
                              "chinese_keywords": ["太阳能花园灯", "户外太阳能灯"],
                              "variation_keywords": ["waterproof solar light"],
                              "confidence": 0.91
                            }
                            """
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        expander = OpenAICompatibleKeywordExpander(
            settings=Settings(
                _env_file=None,
                openai_api_key="test-key",
                openai_base_url="https://api.example.test/v1",
                openai_model="test-model",
            ),
            client=client,
        )

        expansion = await expander.expand("solar garden light")

    assert expansion.source == "openai_compatible"
    assert expansion.english_keywords == ["solar garden light", "outdoor solar light"]
    assert expansion.chinese_keywords == ["太阳能花园灯", "户外太阳能灯"]
    assert expansion.variation_keywords == ["waterproof solar light"]
    assert expansion.confidence == 0.91


@pytest.mark.anyio
async def test_expand_keywords_falls_back_when_openai_key_is_missing():
    settings = Settings(_env_file=None, openai_api_key=None)

    expansion = await expand_keywords("handheld fan", settings=settings)

    assert expansion.source == "deterministic_v1"
    assert "手持风扇" in expansion.chinese_keywords
