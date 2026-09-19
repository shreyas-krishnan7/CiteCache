import { useState } from "react";
import { Link } from "react-router-dom";
import { LAST_ANSWER_PREFIX, useAuth } from "../../context/AuthContext.jsx";
import { useDocuments } from "../../context/DocumentsContext.jsx";
import { api } from "../../lib/api.js";
import { AlertIcon, ArrowRightIcon, QueryIcon, SearchIcon, Spinner } from "../icons.jsx";
import AnswerView from "./AnswerView.jsx";
import EvidencePanel from "./EvidencePanel.jsx";

// The last answer survives switching to Documents and back (per browser tab,
// per user; AuthContext clears it on sign-out).
const storageKey = (username) => `${LAST_ANSWER_PREFIX}${username}`;

function loadLast(username) {
  try {
    return JSON.parse(sessionStorage.getItem(storageKey(username))) ?? null;
  } catch {
    return null;
  }
}

export default function QueryWorkspace() {
  const { documents, loaded } = useDocuments();
  const { user } = useAuth();
  const [answered, setAnswered] = useState(() => loadLast(user.username));
  const [draft, setDraft] = useState(() => answered?.question ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function onSubmit(e) {
    e.preventDefault();
    const question = draft.trim();
    if (!question || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.ask(question);
      const next = { question, result };
      setAnswered(next);
      try { sessionStorage.setItem(storageKey(user.username), JSON.stringify(next)); } catch { /* storage unavailable */ }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const noDocuments = loaded && documents.length === 0;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto xl:flex-row xl:overflow-hidden">
      <section className="flex min-w-0 flex-1 flex-col xl:overflow-y-auto">
        <div className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-6 py-6 backdrop-blur lg:px-10">
          <form onSubmit={onSubmit} className="mx-auto flex max-w-3xl items-center gap-3 rounded-xl border border-slate-300 bg-white py-2 pl-5 pr-2 shadow-sm focus-within:border-blue-600 focus-within:ring-3 focus-within:ring-blue-600/15">
            <SearchIcon className="size-5 shrink-0 text-slate-500" />
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder={noDocuments ? "Upload a document first…" : "Ask a question about your documents…"}
              aria-label="Question"
              disabled={noDocuments}
              className="min-w-0 flex-1 bg-transparent py-2 text-[17px] text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!draft.trim() || loading || noDocuments}
              aria-label="Ask"
              className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700 transition hover:bg-blue-100 disabled:opacity-40"
            >
              {loading ? <Spinner className="size-5" /> : <ArrowRightIcon className="size-5" />}
            </button>
          </form>
        </div>

        <div className="mx-auto w-full max-w-3xl px-6 py-12 lg:px-10">
          {error && (
            <div role="alert" className="mb-8 flex items-start gap-2.5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              <AlertIcon className="mt-0.5 size-4 shrink-0" /> {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center gap-3 text-slate-500">
              <Spinner className="size-5" />
              Searching your documents, drafting an answer and checking every citation…
            </div>
          ) : answered ? (
            <AnswerView question={answered.question} result={answered.result} />
          ) : noDocuments ? (
            <div className="rounded-xl border border-slate-200 px-8 py-12 text-center">
              <p className="text-lg font-semibold">No documents to search yet</p>
              <p className="mt-2 text-sm text-slate-500">Upload a document and it can be queried as soon as it's indexed.</p>
              <Link to="/documents" className="mt-6 inline-flex items-center gap-2 rounded-md bg-blue-700 px-4 py-2.5 font-mono text-sm text-white hover:bg-blue-800">
                Go to Documents <ArrowRightIcon className="size-4" />
              </Link>
            </div>
          ) : (
            <div className="pt-10 text-center">
              <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-blue-50 text-blue-700">
                <QueryIcon className="size-6" />
              </div>
              <p className="mt-5 text-2xl font-bold tracking-tight">Ask your documents anything</p>
              <p className="mx-auto mt-2 max-w-md text-slate-500">
                Every answer cites the passages it comes from, and each citation is checked before you see it.
              </p>
            </div>
          )}
        </div>
      </section>

      <EvidencePanel result={loading ? null : answered?.result} loading={loading} />
    </div>
  );
}
