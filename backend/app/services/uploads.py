import hashlib
import re
from datetime import UTC, datetime
from io import BytesIO

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from app.models import PaperResult, UploadSummaryResponse
from app.services.claude import summarise_with_claude

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_SUMMARY_CHARS = 12000
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/octet-stream",
}


async def summarise_upload(file: UploadFile) -> UploadSummaryResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Upload a PDF, TXT, or Markdown file")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload must be 8 MB or smaller")

    text = _extract_text(file.filename, file.content_type or "", content)
    cleaned = _clean_text(text)
    if len(cleaned) < 120:
        raise HTTPException(status_code=400, detail="Could not extract enough readable text from this file")

    digest = hashlib.sha256(content).hexdigest()[:12]
    title = _guess_title(file.filename, cleaned)
    paper = PaperResult(
        id=f"upload-{digest}",
        title=title,
        authors=["Uploaded document"],
        abstract=cleaned[:MAX_SUMMARY_CHARS],
        published=datetime.now(UTC),
        categories=["uploaded", _suffix_category(file.filename)],
        url=f"local-upload://{file.filename}",
    )
    summary = await summarise_with_claude(paper)
    return UploadSummaryResponse(paper=paper, summary=summary)


def _extract_text(filename: str, content_type: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if content_type == "application/pdf" or suffix == "pdf":
        try:
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Could not read text from this PDF") from exc

    if suffix in {"txt", "md"} or content_type.startswith("text/") or content_type == "application/octet-stream":
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
    raise HTTPException(status_code=400, detail="Unsupported upload format")


def _guess_title(filename: str, text: str) -> str:
    for line in text.splitlines()[:12]:
        candidate = line.strip(" #\t")
        if 8 <= len(candidate) <= 160 and not candidate.lower().startswith(("abstract", "introduction")):
            return candidate
    return re.sub(r"[_-]+", " ", filename.rsplit(".", 1)[0]).strip().title()


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _suffix_category(filename: str) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else "document"
    return f"file.{suffix}"
