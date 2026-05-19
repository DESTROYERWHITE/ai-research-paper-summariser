import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Bookmark, Clipboard, Download, ExternalLink, Loader2, Search, Trash2 } from "lucide-react";
import { api } from "./api";
import "./styles.css";

const starterQueries = ["RAG", "LLM evaluation", "agentic workflows", "transformers"];

function App() {
  const [query, setQuery] = useState("retrieval augmented generation");
  const [papers, setPapers] = useState([]);
  const [library, setLibrary] = useState([]);
  const [summaries, setSummaries] = useState({});
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [activeSummary, setActiveSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    refreshLibrary();
  }, []);

  async function refreshLibrary() {
    try {
      setLibrary(await api.library());
    } catch (err) {
      setError(err.message);
    }
  }

  async function runSearch(nextQuery = query) {
    setError("");
    setLoadingSearch(true);
    try {
      const data = await api.search(nextQuery);
      setPapers(data.papers);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSearch(false);
    }
  }

  async function summarise(paper) {
    setError("");
    setActiveSummary(paper.id);
    try {
      const summary = await api.summarise(paper.id);
      setSummaries((current) => ({ ...current, [paper.id]: summary }));
    } catch (err) {
      setError(err.message);
    } finally {
      setActiveSummary(null);
    }
  }

  async function savePaper(paper) {
    const summary = summaries[paper.id];
    if (!summary) {
      await summarise(paper);
      return;
    }
    await api.save(paper, summary, paper.categories.slice(0, 3));
    refreshLibrary();
  }

  async function copyMarkdown() {
    const response = await fetch(api.markdownUrl);
    const markdown = await response.text();
    await navigator.clipboard.writeText(markdown);
  }

  const savedIds = useMemo(() => new Set(library.map((entry) => entry.paper.id)), [library]);

  return (
    <main className="shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Python + AI Portfolio Project</p>
            <h1>AI Research Paper Summariser</h1>
          </div>
          <a className="iconLink" href="https://arxiv.org" target="_blank" rel="noreferrer" title="Open arXiv">
            <ExternalLink size={18} />
          </a>
        </header>

        <form
          className="searchRow"
          onSubmit={(event) => {
            event.preventDefault();
            runSearch();
          }}
        >
          <Search size={20} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search keyword or arXiv ID" />
          <button type="submit" disabled={loadingSearch}>
            {loadingSearch ? <Loader2 className="spin" size={18} /> : "Search"}
          </button>
        </form>

        <div className="chips">
          {starterQueries.map((item) => (
            <button
              key={item}
              onClick={() => {
                setQuery(item);
                runSearch(item);
              }}
            >
              {item}
            </button>
          ))}
        </div>

        {error && <div className="error">{error}</div>}

        {loadingSearch ? (
          <div className="resultsGrid">
            {[1, 2, 3].map((item) => (
              <div className="paperCard skeleton" key={item} />
            ))}
          </div>
        ) : (
          <div className="resultsGrid">
            {papers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                summary={summaries[paper.id]}
                loading={activeSummary === paper.id}
                saved={savedIds.has(paper.id)}
                onSummarise={() => summarise(paper)}
                onSave={() => savePaper(paper)}
              />
            ))}
          </div>
        )}
      </section>

      <aside className="libraryPanel">
        <div className="libraryHeader">
          <div>
            <p className="eyebrow">Reading List</p>
            <h2>{library.length} saved</h2>
          </div>
          <div className="libraryActions">
            <button title="Copy Markdown" onClick={copyMarkdown}>
              <Clipboard size={17} />
            </button>
            <a title="Download DOCX" href={api.docxUrl}>
              <Download size={17} />
            </a>
          </div>
        </div>
        <div className="savedList">
          {library.map((entry) => (
            <article key={entry.id} className="savedItem">
              <div>
                <strong>{entry.paper.title}</strong>
                <span>{entry.paper.categories.slice(0, 2).join(" / ")}</span>
              </div>
              <button title="Remove" onClick={async () => { await api.remove(entry.id); refreshLibrary(); }}>
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      </aside>
    </main>
  );
}

function PaperCard({ paper, summary, loading, saved, onSummarise, onSave }) {
  return (
    <article className="paperCard">
      <div className="paperMeta">
        <span>{paper.id}</span>
        <span>{new Date(paper.published).getFullYear()}</span>
      </div>
      <h2>{paper.title}</h2>
      <p className="authors">{paper.authors.slice(0, 4).join(", ")}</p>
      <p className="abstract">{paper.abstract}</p>
      <div className="tagRow">
        {paper.categories.slice(0, 4).map((category) => (
          <span key={category}>{category}</span>
        ))}
      </div>
      <div className="cardActions">
        <button onClick={onSummarise} disabled={loading}>
          {loading ? <Loader2 className="spin" size={17} /> : "AI summary"}
        </button>
        <button className="secondary" onClick={onSave} disabled={saved}>
          <Bookmark size={17} />
          {saved ? "Saved" : "Save"}
        </button>
      </div>
      {(loading || summary) && (
        <section className="summaryPanel">
          {loading ? (
            <p className="typing">Generating structured summary...</p>
          ) : (
            <>
              <h3>Summary</h3>
              <ul>{summary.summary_bullets.map((item) => <li key={item}>{item}</li>)}</ul>
              <h3>Contributions</h3>
              <ul>{summary.contributions.map((item) => <li key={item}>{item}</li>)}</ul>
              <h3>Limitations</h3>
              <ul>{summary.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
            </>
          )}
        </section>
      )}
    </article>
  );
}

createRoot(document.getElementById("root")).render(<App />);
