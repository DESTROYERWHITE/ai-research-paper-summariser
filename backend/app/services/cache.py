import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import DATA_DIR, get_settings


class JsonCache:
    def __init__(self, path: Path, ttl_hours: int | None = None) -> None:
        self.path = path
        self.ttl = timedelta(hours=ttl_hours or get_settings().cache_ttl_hours)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def get(self, key: str) -> Any | None:
        data = self._read()
        item = data.get(key)
        if not item:
            return None

        cached_at = datetime.fromisoformat(item["cached_at"])
        if datetime.now(UTC) - cached_at > self.ttl:
            return None
        return item["value"]

    async def set(self, key: str, value: Any) -> None:
        data = self._read()
        data[key] = {"cached_at": datetime.now(UTC).isoformat(), "value": value}
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))


arxiv_cache = JsonCache(DATA_DIR / "arxiv_cache.json")
summary_cache = JsonCache(DATA_DIR / "summary_cache.json", ttl_hours=24 * 14)
