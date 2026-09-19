import { useState } from "react";
import { percent, sectionBadge } from "../../lib/format.js";
import { CheckIcon, ChevronDownIcon, FlowIcon } from "../icons.jsx";
import ProgressBar from "../ProgressBar.jsx";

function ScoreRow({ label, value, hint }) {
  const pct = percent(value);
  return (
    <div title={hint}>
      <div className="flex justify-between font-mono text-xs text-slate-600">
        <span>{label}</span>
        <span className="tabular-nums">{pct}%</span>
      </div>
      <ProgressBar value={pct} className="mt-1.5 h-1" label={label} />
    </div>
  );
}

export default function RetrievalTransparency({ result }) {
  const [open, setOpen] = useState(false);
  const cb = result.confidence_breakdown;
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-3.5 font-mono text-sm text-slate-700 hover:bg-slate-50"
      >
        <FlowIcon className="size-4.5 text-slate-500" />
        Retrieval Transparency
        <ChevronDownIcon className={`ml-auto size-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="max-h-80 space-y-5 overflow-y-auto border-t border-slate-100 px-4 py-4">
          {result.source === "cache" ? (
            <p className="text-sm leading-relaxed text-slate-600">
              Served from the semantic cache: this question closely matched one answered earlier, so retrieval
              and generation were skipped. Its confidence ({percent(result.confidence)}%) was recorded when it was first generated.
            </p>
          ) : (
            <>
              {cb && (
                <div className="space-y-3">
                  <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-slate-400">Confidence breakdown</p>
                  <ScoreRow label="Retrieval similarity" value={cb.retrieval_score} hint="Similarity of the best passage to your question" />
                  <ScoreRow label="Citations verified" value={cb.citation_support_rate} hint="Share of cited claims confirmed by their passage" />
                  <ScoreRow label="Completeness" value={cb.completeness} hint="Lower when the documents don't fully answer the question" />
                </div>
              )}
              <div>
                <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-slate-400">
                  {result.retrieved.length} passages retrieved · hybrid search + rerank
                </p>
                <ol className="mt-2 space-y-1.5">
                  {result.retrieved.map((c, i) => (
                    <li key={c.chunk_id} className="flex items-center gap-2 font-mono text-xs text-slate-600">
                      <span className="w-4 shrink-0 text-right tabular-nums text-slate-400">{i + 1}</span>
                      <span className="min-w-0 flex-1 truncate" title={`${c.document} · ${c.section ?? ""}`}>
                        {c.document}{c.section ? ` · ${sectionBadge(c.section)}` : ""}
                      </span>
                      {c.dense_score != null && <span className="tabular-nums text-slate-400">{percent(c.dense_score)}%</span>}
                      {c.cited ? <CheckIcon className="size-3.5 text-emerald-600" aria-label="cited" /> : <span className="size-3.5" />}
                    </li>
                  ))}
                </ol>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
