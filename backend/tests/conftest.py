import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def disable_ai_provider_for_tests(monkeypatch):
    monkeypatch.setenv("AI_KEYWORD_EXPANSION_ENABLED", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
