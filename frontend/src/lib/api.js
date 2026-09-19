export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = () => {};

/** Called whenever the server says the session is gone (expired or signed out elsewhere). */
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

function messageFrom(data, status) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    // FastAPI/Pydantic validation errors: "Value error, Password must be ..."
    return detail.map((d) => String(d.msg || "").replace(/^Value error, /, "")).join(" ");
  }
  return `Request failed (${status}).`;
}

async function request(path, { method = "GET", json, form } = {}) {
  let res;
  try {
    res = await fetch(path, {
      method,
      credentials: "same-origin",
      headers: json !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: form ?? (json !== undefined ? JSON.stringify(json) : undefined),
    });
  } catch {
    throw new ApiError(0, "Can't reach the CiteCache server. Is the API running?");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth/")) onUnauthorized();
    throw new ApiError(res.status, messageFrom(data, res.status));
  }
  return data;
}

export const api = {
  me: () => request("/auth/me"),
  login: (username, password) => request("/auth/login", { method: "POST", json: { username, password } }),
  signup: (username, password) => request("/auth/signup", { method: "POST", json: { username, password } }),
  logout: () => request("/auth/logout", { method: "POST" }),

  documents: () => request("/workspace/documents"),
  jobs: () => request("/workspace/jobs"),
  upload: (files) => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    return request("/workspace/upload", { method: "POST", form });
  },
  ask: (question) => request("/workspace/ask", { method: "POST", json: { question } }),
};
