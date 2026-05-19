import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.config import DATA_DIR
from app.models import LibraryEntry, SaveLibraryRequest

LIBRARY_PATH = DATA_DIR / "library.json"


async def list_library() -> list[LibraryEntry]:
    return [LibraryEntry.model_validate(item) for item in _read()]


async def save_entry(request: SaveLibraryRequest) -> LibraryEntry:
    entries = _read()
    existing = next((item for item in entries if item["paper"]["id"] == request.paper.id), None)
    entry = LibraryEntry(
        id=existing["id"] if existing else str(uuid4()),
        paper=request.paper,
        summary=request.summary,
        tags=request.tags,
        saved_at=datetime.now(UTC),
    )
    entries = [item for item in entries if item["id"] != entry.id]
    entries.insert(0, entry.model_dump(mode="json"))
    _write(entries)
    return entry


async def delete_entry(entry_id: str) -> bool:
    entries = _read()
    next_entries = [item for item in entries if item["id"] != entry_id]
    _write(next_entries)
    return len(next_entries) != len(entries)


def _read() -> list[dict]:
    if not Path(LIBRARY_PATH).exists():
        return []
    return json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))


def _write(entries: list[dict]) -> None:
    LIBRARY_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")
