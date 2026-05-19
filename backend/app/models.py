from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaperResult(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str
    published: datetime
    categories: list[str] = Field(default_factory=list)
    url: str


class SearchResponse(BaseModel):
    query: str
    count: int
    papers: list[PaperResult]
    source: Literal["arxiv", "cache", "upload"]


class SummariseRequest(BaseModel):
    paper_id: str


class SummaryResponse(BaseModel):
    paper_id: str
    summary_bullets: list[str] = Field(min_length=3, max_length=3)
    contributions: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    follow_up_papers: list[str] = Field(default_factory=list)

    @field_validator("summary_bullets", "contributions", "limitations", "follow_up_papers")
    @classmethod
    def strip_empty_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class LibraryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    paper: PaperResult
    summary: SummaryResponse
    tags: list[str] = Field(default_factory=list)
    saved_at: datetime


class SaveLibraryRequest(BaseModel):
    paper: PaperResult
    summary: SummaryResponse
    tags: list[str] = Field(default_factory=list)


class UploadSummaryResponse(BaseModel):
    paper: PaperResult
    summary: SummaryResponse
