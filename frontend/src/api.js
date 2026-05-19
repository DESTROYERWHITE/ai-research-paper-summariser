const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  search: (query) => request(`/search?q=${encodeURIComponent(query)}`),
  summarise: (paperId) =>
    request("/summarise", {
      method: "POST",
      body: JSON.stringify({ paper_id: paperId }),
    }),
  library: () => request("/library"),
  save: (paper, summary, tags) =>
    request("/library", {
      method: "POST",
      body: JSON.stringify({ paper, summary, tags }),
    }),
  remove: (id) => request(`/library/${id}`, { method: "DELETE" }),
  markdownUrl: `${API_BASE}/export/markdown`,
  docxUrl: `${API_BASE}/export/docx`,
};
