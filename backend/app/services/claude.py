import json

import httpx
from fastapi import HTTPException

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


def _fallback_summary(paper: PaperResult) -> SummaryResponse:
    return SummaryResponse(
        paper_id=paper.id,
        summary_bullets=[
            f"{paper.title} addresses a research problem in {', '.join(paper.categories[:2]) or 'its field'}.",
            paper.abstract[:260].rstrip() + ("..." if len(paper.abstract) > 260 else ""),
            "Use the Claude API key to generate a richer structured summary from the live model.",
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
    cached = await summary_cache.get(paper.id)
    if cached:
        return SummaryResponse.model_validate(cached)

    settings = get_settings()
    if not settings.anthropic_api_key:
        summary = _fallback_summary(paper)
        await summary_cache.set(paper.id, summary.model_dump(mode="json"))
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
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
    except httpx.RequestError:
        summary = _fallback_summary(paper)
        await summary_cache.set(paper.id, summary.model_dump(mode="json"))
        return summary
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Claude API summarisation failed")

    text = response.json()["content"][0]["text"]
    try:
        parsed = json.loads(text)
        summary = SummaryResponse(paper_id=paper.id, **parsed)
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Claude returned invalid summary JSON") from exc

    await summary_cache.set(paper.id, summary.model_dump(mode="json"))
    return summary
