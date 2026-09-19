import { useState } from "react";
import { percent, sectionBadge } from "../../lib/format.js";
import { AlertIcon, BadgeCheckIcon, ChevronDownIcon, DocTypeIcon } from "../icons.jsx";
import RetrievalTransparency from "./RetrievalTransparency.jsx";

function MatchPill({ similarity }) {
  const pct = percent(similarity);
  if (pct == null) return null;
  // Calibrated on this embedding model: unrelated passage pairs score a median
  // ~0.60, so only 0.70+ reads as a strong match.
  const tone = pct >= 70 ? "bg-emerald-50 text-emerald-700" : pct >= 60 ? "bg-amber-50 text-amber-800" : "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-mono text-[13px] ${tone}`}
          title="Semantic similarity between your question and this passage">
      <BadgeCheckIcon className="size-4" /> {pct}% Match
    </span>
  );
}

function VerdictPill({ supported }) {
  if (supported == null) return null;
  return supported ? (
    <span className="font-mono text-xs text-emerald-700" title="Every claim citing this passage was checked against it">Verified</span>
  ) : (
    <span className="inline-flex items-center gap-1 font-mono text-xs text-red-700" title="A claim citing this passage was not supported by it">
      <AlertIcon className="size-3.5" /> Not supported
    </span>
  );
}

function EvidenceCard({ item }) {
  const [open, setOpen] = useState(false);
  const badge = sectionBadge(item.section);
  return (
    <li className="rounded-lg border border-l-4 border-slate-200 border-l-slate-300 bg-white p-5 shadow-xs">
      <div className="flex items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-blue-50 text-blue-700">
          <DocTypeIcon filename={item.document} className="size-4.5" />
        </div>
        <p className="min-w-0 flex-1 truncate pt-1.5 font-mono text-sm font-semibold text-blue-700" title={item.document}>
          {item.document}
        </p>
        {badge && (
          <span className="shrink-0 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 font-mono text-xs text-slate-600" title={item.section}>
            {badge}
          </span>
        )}
      </div>

      <p className="mt-4 line-clamp-4 text-[15px] leading-relaxed text-slate-700">“{item.snippet}”</p>

      {item.claims.length > 0 && open && (
        <ul className="mt-4 space-y-2 border-t border-slate-100 pt-4">
          {item.claims.map((c, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-600">
              <span className={`mt-2 size-1.5 shrink-0 rounded-full ${c.supported === false ? "bg-red-500" : "bg-emerald-500"}`} />
              {c.text}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4">
        <MatchPill similarity={item.similarity} />
        <VerdictPill supported={item.supported} />
        {item.claims.length > 0 && (
          <button type="button" onClick={() => setOpen((o) => !o)}
                  className="ml-auto flex items-center gap-1 font-mono text-xs text-slate-500 hover:text-slate-800">
            {item.claims.length} claim{item.claims.length === 1 ? "" : "s"}
            <ChevronDownIcon className={`size-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        )}
      </div>
    </li>
  );
}

export default function EvidencePanel({ result, loading }) {
  const evidence = result?.evidence ?? [];
  return (
    <aside className="flex shrink-0 flex-col border-t border-slate-200 bg-slate-50/70 xl:h-full xl:w-[27rem] xl:border-l xl:border-t-0">
      <div className="flex items-center justify-between border-b border-slate-200 px-7 py-6">
        <h2 className="text-xl font-semibold tracking-tight">Evidence &amp; Citations</h2>
        {result && (
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 font-mono text-xs text-slate-600">
            {evidence.length} Source{evidence.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        {loading ? (
          <ul className="space-y-4" aria-hidden="true">
            {[0, 1, 2].map((i) => <li key={i} className="h-44 animate-pulse rounded-lg bg-slate-200/60" />)}
          </ul>
        ) : evidence.length ? (
          <ul className="space-y-5">
            {evidence.map((item) => <EvidenceCard key={item.chunk_id} item={item} />)}
          </ul>
        ) : (
          <p className="px-1 text-sm leading-relaxed text-slate-500">
            {result
              ? "No passages were cited for this answer."
              : "Passages your answer relies on appear here, each checked against the claim it supports."}
          </p>
        )}
      </div>

      {result && !loading && (
        <div className="border-t border-slate-200 p-5">
          <RetrievalTransparency result={result} />
        </div>
      )}
    </aside>
  );
}
