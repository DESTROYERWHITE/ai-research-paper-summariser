import json

import httpx
from app.config import get_settings
from app.models import PaperResult, SummaryResponse
from app.services.cache import summary_cache


SYSTEM_PROMPT = """You are an expert ML research assistant.
Return only valid JSON using exactly these keys:
summary_bullets: an array of exactly 3 concise bullets.
contributions: an array of the paper's key technical contributions.
limitations: an array of limitations, assumptions, or risks identified from the abstract.
follow_up_papers: an array of 3 relevant follow-up paper titles or search phrases.
Do not include markdown fences or commentary."""

PLACEHOLDER_KEYS = {
    "",
    "your_claude_api_key_here",
    "your_anthropic_api_key_here",
    "your_gemini_api_key_here",
    "sk-ant-your-key",
}


def _fallback_summary(paper: PaperResult) -> SummaryResponse:
    return SummaryResponse(
        paper_id=paper.id,
        summary_bullets=[
            f"{paper.title} addresses a research problem in {', '.join(paper.categories[:2]) or 'its field'}.",
            paper.abstract[:260].rstrip() + ("..." if len(paper.abstract) > 260 else ""),
            "Add a working Gemini or Claude API key to generate a richer structured summary from a live model.",
        ],
        contributions=[
            "Extracted metadata and paper text for structured analysis.",
            "Prepared the paper for LLM-based structured analysis.",
        ],
        limitations=[
            "Fallback summary uses the available extracted text rather than full model reasoning.",
            "Live Claude output will provide stronger synthesis when an API key is configured.",
        ],
        follow_up_papers=[
            f"{paper.categories[0]} survey recent advances" if paper.categories else "recent related survey",
            "benchmark datasets for this research area",
            "limitations of abstract-only paper summarisation",
        ],
    )


async def summarise_with_claude(paper: PaperResult) -> SummaryResponse:
    settings = get_settings()
    provider, cache_key = _provider_and_cache_key(settings, paper.id)
    cached = await summary_cache.get(cache_key)
    if cached:
        return SummaryResponse.model_validate(cached)

    if provider == "gemini":
        summary = await _summarise_with_gemini(paper, settings)
        await summary_cache.set(cache_key, summary.model_dump(mode="json"))
        return summary

    api_key = (settings.anthropic_api_key or "").strip()
    if api_key.lower() in PLACEHOLDER_KEYS:
        summary = _fallback_summary(paper)
        await summary_cache.set(cache_key, summary.model_dump(mode="json"))
        return summary

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 900,
        "temperature": 0.2,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"Title: {paper.title}\n\nAbstract: {paper.abstract}",
            }
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, trust_env=False) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
    except httpx.RequestError:
        summary = _fallback_summary(paper)
        await summary_cache.set(cache_key, summary.model_dump(mode="json"))
        return summary
    if response.status_code >= 400:
        summary = _fallback_summary(paper)
        await summary_cache.set(cache_key, summary.model_dump(mode="json"))
        return summary

    text = response.json()["content"][0]["text"]
    try:
        parsed = json.loads(text)
        summary = SummaryResponse(paper_id=paper.id, **parsed)
    except (KeyError, json.JSONDecodeError, ValueError):
        summary = _fallback_summary(paper)

    await summary_cache.set(cache_key, summary.model_dump(mode="json"))
    return summary


def _provider_and_cache_key(settings, paper_id: str) -> tuple[str, str]:
    gemini_key = (settings.gemini_api_key or "").strip()
    if gemini_key and gemini_key.lower() not in PLACEHOLDER_KEYS:
        return "gemini", f"gemini:{settings.gemini_model}:{paper_id}"
    anthropic_key = (settings.anthropic_api_key or "").strip()
    if anthropic_key and anthropic_key.lower() not in PLACEHOLDER_KEYS:
        return "claude", f"claude:{settings.anthropic_model}:{paper_id}"
    return "fallback", f"fallback:{paper_id}"


async def _summarise_with_gemini(paper: PaperResult, settings) -> SummaryResponse:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Title: {paper.title}\n\nAbstract or extracted paper text: {paper.abstract}"}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, trust_env=False) as client:
            response = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
    except httpx.RequestError:
        return _fallback_summary(paper)
    if response.status_code >= 400:
        return _fallback_summary(paper)

    try:
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        return SummaryResponse(paper_id=paper.id, **parsed)
    except (KeyError, IndexError, json.JSONDecodeError, ValueError):
        return _fallback_summary(paper)
