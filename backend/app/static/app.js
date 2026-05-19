const state = {
  papers: [],
  summaries: {},
  library: [],
};

const elements = {
  form: document.querySelector("#search-form"),
  query: document.querySelector("#query"),
  results: document.querySelector("#results"),
  notice: document.querySelector("#notice"),
  status: document.querySelector("#status-pill"),
  savedCount: document.querySelector("#saved-count"),
  savedList: document.querySelector("#saved-list"),
  copyMarkdown: document.querySelector("#copy-markdown"),
};

function setStatus(text) {
  elements.status.textContent = text;
}

function showNotice(message) {
  elements.notice.textContent = message;
  elements.notice.classList.toggle("hidden", !message);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }
  return response.status === 204 ? null : response.json();
}

function renderSkeletons() {
  elements.results.innerHTML = [1, 2, 3].map(() => '<article class="skeleton"></article>').join("");
}

function renderPapers() {
  const savedIds = new Set(state.library.map((entry) => entry.paper.id));
  elements.results.innerHTML = state.papers.map((paper) => paperCard(paper, savedIds.has(paper.id))).join("");
}

function paperCard(paper, saved) {
  const summary = state.summaries[paper.id];
  const published = new Date(paper.published).getFullYear();
  const tags = paper.categories.slice(0, 4).map((category) => `<span>${escapeHtml(category)}</span>`).join("");
  const authors = paper.authors.slice(0, 4).map(escapeHtml).join(", ");
  return `
    <article class="paper-card" data-paper-id="${escapeHtml(paper.id)}">
      <div class="meta">
        <span>${escapeHtml(paper.id)}</span>
        <span>${published}</span>
      </div>
      <h2>${escapeHtml(paper.title)}</h2>
      <p class="authors">${authors}</p>
      <p class="abstract">${escapeHtml(paper.abstract)}</p>
      <div class="tags">${tags}</div>
      <div class="card-actions">
        <button data-action="summarise">${summary ? "Refresh summary" : "AI summary"}</button>
        <button class="secondary" data-action="save" ${saved ? "disabled" : ""}>${saved ? "Saved" : "Save"}</button>
      </div>
      ${summary ? summaryPanel(summary) : ""}
    </article>
  `;
}

function summaryPanel(summary) {
  return `
    <section class="summary">
      <h3>Summary</h3>
      <ul>${summary.summary_bullets.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      <h3>Contributions</h3>
      <ul>${summary.contributions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      <h3>Limitations</h3>
      <ul>${summary.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      <h3>Follow-up Papers</h3>
      <ul>${summary.follow_up_papers.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderLibrary() {
  elements.savedCount.textContent = `${state.library.length} saved`;
  elements.savedList.innerHTML = state.library.length
    ? state.library.map(savedItem).join("")
    : '<p class="authors">Saved summaries will appear here.</p>';
}

function savedItem(entry) {
  const categories = entry.paper.categories.slice(0, 2).map(escapeHtml).join(" / ");
  return `
    <article class="saved-item">
      <div>
        <strong>${escapeHtml(entry.paper.title)}</strong>
        <span>${categories}</span>
      </div>
      <button class="remove" title="Remove" data-remove="${escapeHtml(entry.id)}" aria-label="Remove saved paper">
        <svg viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg>
      </button>
    </article>
  `;
}

async function search(query) {
  showNotice("");
  setStatus("Searching");
  renderSkeletons();
  try {
    const data = await api(`/search?q=${encodeURIComponent(query)}`);
    state.papers = data.papers;
    renderPapers();
    setStatus(data.source === "cache" ? "From cache" : "Live arXiv");
  } catch (error) {
    elements.results.innerHTML = "";
    showNotice(error.message);
    setStatus("Check error");
  }
}

async function summarise(paperId) {
  const card = document.querySelector(`[data-paper-id="${CSS.escape(paperId)}"]`);
  card?.classList.add("loading");
  setStatus("Summarising");
  try {
    state.summaries[paperId] = await api("/summarise", {
      method: "POST",
      body: JSON.stringify({ paper_id: paperId }),
    });
    renderPapers();
    setStatus("Summary ready");
  } catch (error) {
    showNotice(error.message);
    setStatus("Check error");
  } finally {
    card?.classList.remove("loading");
  }
}

async function savePaper(paperId) {
  const paper = state.papers.find((item) => item.id === paperId);
  if (!paper) return;
  if (!state.summaries[paperId]) {
    await summarise(paperId);
  }
  const summary = state.summaries[paperId];
  if (!summary) return;

  await api("/library", {
    method: "POST",
    body: JSON.stringify({ paper, summary, tags: paper.categories.slice(0, 3) }),
  });
  await loadLibrary();
  renderPapers();
  setStatus("Saved");
}

async function loadLibrary() {
  state.library = await api("/library");
  renderLibrary();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  search(elements.query.value.trim());
});

document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => {
    elements.query.value = button.dataset.query;
    search(button.dataset.query);
  });
});

elements.results.addEventListener("click", (event) => {
  const actionButton = event.target.closest("[data-action]");
  if (!actionButton) return;
  const card = actionButton.closest("[data-paper-id]");
  const paperId = card.dataset.paperId;
  if (actionButton.dataset.action === "summarise") summarise(paperId);
  if (actionButton.dataset.action === "save") savePaper(paperId);
});

elements.savedList.addEventListener("click", async (event) => {
  const removeButton = event.target.closest("[data-remove]");
  if (!removeButton) return;
  await api(`/library/${removeButton.dataset.remove}`, { method: "DELETE" });
  await loadLibrary();
  renderPapers();
  setStatus("Removed");
});

elements.copyMarkdown.addEventListener("click", async () => {
  const response = await fetch("/export/markdown");
  await navigator.clipboard.writeText(await response.text());
  setStatus("Copied");
});

loadLibrary()
  .then(() => search(elements.query.value))
  .catch((error) => showNotice(error.message));
