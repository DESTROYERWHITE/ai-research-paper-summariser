import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus

import httpx

from app.config import get_settings
from app.models import PaperResult, SearchResponse
from app.services.cache import arxiv_cache


ATOM = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def _normalise_arxiv_id(value: str) -> str:
    cleaned = value.strip()
    cleaned = cleaned.removeprefix("https://arxiv.org/abs/")
    cleaned = cleaned.removeprefix("http://arxiv.org/abs/")
    return cleaned


def _cache_key(query: str, max_results: int) -> str:
    digest = hashlib.sha256(f"{query}:{max_results}".encode("utf-8")).hexdigest()[:16]
    return f"search:{digest}"


def _query_url(query: str, max_results: int) -> str:
    settings = get_settings()
    paper_id = _normalise_arxiv_id(query)
    if re.fullmatch(r"[\w.-]+/\d{7}|\d{4}\.\d{4,5}(v\d+)?", paper_id):
        search_query = f"id:{paper_id}"
    else:
        search_query = f"all:{query}"
    return (
        f"{settings.arxiv_base_url}?search_query={quote_plus(search_query)}"
        f"&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    )


def parse_arxiv(xml_body: str) -> list[PaperResult]:
    root = ET.fromstring(xml_body)
    papers: list[PaperResult] = []
    for entry in root.findall("atom:entry", ATOM):
        raw_id = entry.findtext("atom:id", default="", namespaces=ATOM)
        title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM).split())
        abstract = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM).split())
        published = datetime.fromisoformat(
            entry.findtext("atom:published", default="", namespaces=ATOM).replace("Z", "+00:00")
        )
        authors = [
            author.findtext("atom:name", default="", namespaces=ATOM)
            for author in entry.findall("atom:author", ATOM)
        ]
        categories = [
            category.attrib.get("term", "")
            for category in entry.findall("atom:category", ATOM)
            if category.attrib.get("term")
        ]
        papers.append(
            PaperResult(
                id=_normalise_arxiv_id(raw_id.split("/")[-1]),
                title=title,
                authors=authors,
                abstract=abstract,
                published=published,
                categories=categories,
                url=raw_id,
            )
        )
    return papers


async def search_arxiv(query: str, max_results: int = 10) -> SearchResponse:
    key = _cache_key(query, max_results)
    cached = await arxiv_cache.get(key)
    if cached:
        papers = [PaperResult.model_validate(item) for item in cached]
        return SearchResponse(query=query, count=len(papers), papers=papers, source="cache")

    async with httpx.AsyncClient(timeout=get_settings().request_timeout_seconds) as client:
        response = await client.get(_query_url(query, max_results))
        response.raise_for_status()

    papers = parse_arxiv(response.text)
    await arxiv_cache.set(key, [paper.model_dump(mode="json") for paper in papers])
    return SearchResponse(query=query, count=len(papers), papers=papers, source="arxiv")
