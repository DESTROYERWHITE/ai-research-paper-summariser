from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import LibraryEntry, SaveLibraryRequest, SearchResponse, SummariseRequest, SummaryResponse
from app.services.arxiv import search_arxiv
from app.services.claude import summarise_with_claude
from app.services.exporter import library_to_docx, library_to_markdown
from app.services.library import delete_entry, list_library, save_entry

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title=settings.app_name, version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def local_app() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/search", response_model=SearchResponse)
async def search(q: str) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query is required")
    return await search_arxiv(q.strip())


@app.post("/summarise", response_model=SummaryResponse)
async def summarise(request: SummariseRequest) -> SummaryResponse:
    results = await search_arxiv(request.paper_id, max_results=1)
    if not results.papers:
        raise HTTPException(status_code=404, detail="Paper not found")
    return await summarise_with_claude(results.papers[0])


@app.get("/library", response_model=list[LibraryEntry])
async def library() -> list[LibraryEntry]:
    return await list_library()


@app.post("/library", response_model=LibraryEntry, status_code=201)
async def create_library_entry(request: SaveLibraryRequest) -> LibraryEntry:
    return await save_entry(request)


@app.delete("/library/{entry_id}", status_code=204)
async def remove_library_entry(entry_id: str) -> Response:
    deleted = await delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Library entry not found")
    return Response(status_code=204)


@app.get("/export/markdown")
async def export_markdown() -> Response:
    markdown = library_to_markdown(await list_library())
    return Response(markdown, media_type="text/markdown")


@app.get("/export/docx")
async def export_docx() -> Response:
    buffer = library_to_docx(await list_library())
    headers = {"Content-Disposition": 'attachment; filename="paper-summaries.docx"'}
    return Response(
        buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
