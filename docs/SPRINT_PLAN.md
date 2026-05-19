# Sprint Plan: AI Research Paper Summariser

## Sprint Goal
Build and deploy a portfolio-ready AI research tool that searches arXiv, summarises papers with Claude, saves useful results, and exports summaries for later reading.

## Timeline

### Day 1: Backend Foundation
- Create FastAPI app structure and async endpoint contracts.
- Define Pydantic models: `PaperResult`, `SummaryResponse`, `LibraryEntry`.
- Implement arXiv keyword and paper ID search with XML parsing.
- Add local JSON caching to reduce rate-limit pressure.
- Acceptance: `/search?q=` returns validated paper results from arXiv or cache.

### Day 2: LLM Summarisation
- Add Claude API integration with environment-based key loading.
- Write strict JSON system prompt for `summary_bullets`, `contributions`, `limitations`, and `follow_up_papers`.
- Validate model output through Pydantic before returning it.
- Add graceful no-key fallback for local demo mode.
- Acceptance: `/summarise` returns structured JSON for a valid arXiv paper ID.

### Day 3: Library and Export Workflow
- Implement reading list endpoints: `GET /library`, `POST /library`, `DELETE /library/{id}`.
- Persist saved papers locally as JSON.
- Generate Markdown export and `.docx` export with `python-docx`.
- Add backend parser/model tests and 10 preloaded research paper references.
- Acceptance: saved summaries can be exported as Markdown or DOCX.

### Day 4: React Frontend
- Build responsive search interface with result cards and paper category badges.
- Add loading skeletons, error states, and summary generation state.
- Add expandable AI summary panel and reading list sidebar.
- Add copy-to-clipboard Markdown and DOCX download controls.
- Acceptance: user can complete the full search -> summarise -> save -> export flow from the browser.

### Day 5: Polish and Deployment Readiness
- Write README with setup, env vars, API shape, deployment notes, and extension ideas.
- Verify backend syntax/tests and frontend build where dependencies are available.
- Prepare GitHub repository, commit, and push.
- Capture portfolio screenshot after running with a real research topic.
- Acceptance: GitHub repo has a clean commit history and clear local/deployment instructions.

## Backlog
- Full PDF summarisation with PyMuPDF.
- Streaming Claude responses over Server-Sent Events.
- SQLite or Postgres persistence for deployed library storage.
- Authenticated multi-user reading lists.
- Citation export in BibTeX/RIS.
- Background refresh of cached arXiv metadata.

## Risks and Mitigations
- Claude API key unavailable locally: fallback summary keeps the UX demoable while documenting env setup.
- arXiv rate limits: JSON cache stores search results and summary results.
- LLM malformed output: Pydantic validation catches invalid summaries before UI rendering.
- Deployment filesystem persistence: document Postgres/S3-style storage as production extension for Render/Railway.
