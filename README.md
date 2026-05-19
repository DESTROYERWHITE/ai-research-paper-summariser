# AI Research Paper Summariser

Portfolio project for Python + AI roles. It searches arXiv, summarises papers with Gemini or Claude, saves a reading list, and exports saved summaries as Markdown or `.docx`.

## One-Click Local App
On Windows, double-click:

```text
RUN_SUMMARISER.bat
```

The launcher will:
- create `backend/.env` from `backend/.env.example` if needed
- install missing Python backend dependencies
- start the local FastAPI app
- open `http://127.0.0.1:8000` in your browser

Close the launcher window to stop the app.

## Tech Stack
- Backend: FastAPI, async `httpx`, Pydantic, python-dotenv, python-docx
- AI: Gemini API primary, optional Claude fallback, strict structured JSON output
- Data source: arXiv REST API and XML parsing
- Frontend: local FastAPI-served app for one-click use, plus React + Vite source for deployment
- Storage: local JSON cache/library files for a simple deployable prototype

## Features
- Search arXiv by keyword or paper ID.
- Upload local `.pdf`, `.txt`, or `.md` papers for summarisation.
- Parse title, authors, abstract, published date, categories, and URL.
- Cache arXiv and summary responses locally to reduce repeat API calls.
- Summarise each paper into:
  - 3 summary bullets
  - key contributions
  - identified limitations
  - suggested follow-up papers
- Save papers into a reading list.
- Export saved summaries as Markdown or DOCX.
- Use loading skeletons, error states, and generation indicators in the UI.

## Local Setup

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Set your Gemini key in `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
ANTHROPIC_API_KEY=your_claude_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
FRONTEND_ORIGIN=http://localhost:5173
```

The app intentionally does not require a key for local exploration. Without `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`, it returns a clearly marked fallback summary so the full workflow remains demoable.

### Frontend
```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open `http://localhost:5173`.

The one-click local version is served by FastAPI at `http://127.0.0.1:8000`, so it works even when Node/npm is not installed.

## API
- `GET /search?q=keyword_or_arxiv_id`
- `POST /summarise` with body `{ "paper_id": "1706.03762" }`
- `POST /upload` with multipart form field `file`
- `GET /library`
- `POST /library`
- `DELETE /library/{id}`
- `GET /export/markdown`
- `GET /export/docx`

## Security Notes
- API keys are loaded from `.env` via `python-dotenv`.
- `.env` files are ignored by git.
- `backend/.env.example` documents required variables without committing secrets.

## Testing
```bash
cd backend
pytest
```

The repo includes 10 preloaded research paper references in `backend/tests/fixtures_research_papers.json` for demo topics and portfolio screenshots.

## Deployment Notes
- Deploy the FastAPI backend to Render or Railway.
- Add `GEMINI_API_KEY`, `GEMINI_MODEL`, and `FRONTEND_ORIGIN` as backend environment variables. Optionally add `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` as a fallback provider.
- Deploy the React frontend to Vercel.
- Add `VITE_API_BASE_URL` pointing to the backend URL.
- For production persistence, replace JSON files with Postgres or another managed datastore.

## Extension Ideas
- Summarise full PDFs with PyMuPDF instead of abstract-only summaries.
- Add drag-and-drop upload batches for multiple papers at once.
- Stream Claude output with Server-Sent Events.
- Add BibTeX/RIS citation export.
- Add user accounts and per-user reading lists.

## Sprint Plan
See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md).
