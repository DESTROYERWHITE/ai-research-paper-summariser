import pytest
from pydantic import ValidationError

from app.models import PaperResult, SummaryResponse
from app.services.claude import _provider_and_cache_key, summarise_with_claude
from app.services import claude
from datetime import UTC, datetime


def test_summary_requires_three_bullets() -> None:
    with pytest.raises(ValidationError):
        SummaryResponse(
            paper_id="2401.12345",
            summary_bullets=["one", "two"],
            contributions=["contribution"],
            limitations=["limitation"],
            follow_up_papers=["follow up"],
        )


def test_summary_strips_empty_items() -> None:
    summary = SummaryResponse(
        paper_id="2401.12345",
        summary_bullets=[" one ", "two", "three"],
        contributions=[" method ", ""],
        limitations=[" data only "],
        follow_up_papers=[" related work "],
    )

    assert summary.contributions == ["method"]
    assert summary.limitations == ["data only"]


@pytest.mark.asyncio
async def test_placeholder_api_key_uses_fallback(monkeypatch) -> None:
    class Settings:
        gemini_api_key = None
        gemini_model = "gemini-2.5-flash"
        anthropic_api_key = "your_claude_api_key_here"
        anthropic_model = "claude-3-5-sonnet-20241022"
        request_timeout_seconds = 1

    async def fake_cache_get(_key: str):
        return None

    async def fake_cache_set(_key: str, _value):
        return None

    monkeypatch.setattr(claude, "get_settings", lambda: Settings())
    monkeypatch.setattr(claude.summary_cache, "get", fake_cache_get)
    monkeypatch.setattr(claude.summary_cache, "set", fake_cache_set)

    paper = PaperResult(
        id="upload-test",
        title="Uploaded AI Paper",
        authors=["Uploaded document"],
        abstract="This paper studies local summarisation for research workflows.",
        published=datetime.now(UTC),
        categories=["uploaded"],
        url="local-upload://paper.txt",
    )

    summary = await summarise_with_claude(paper)

    assert summary.paper_id == "upload-test"
    assert len(summary.summary_bullets) == 3
    assert "Gemini or Claude API key" in summary.summary_bullets[2]


def test_gemini_key_is_primary_provider() -> None:
    class Settings:
        gemini_api_key = "real-gemini-key"
        gemini_model = "gemini-2.5-flash"
        anthropic_api_key = "real-claude-key"
        anthropic_model = "claude-3-5-sonnet-20241022"

    provider, cache_key = _provider_and_cache_key(Settings(), "paper-1")

    assert provider == "gemini"
    assert cache_key == "gemini:gemini-2.5-flash:paper-1"
