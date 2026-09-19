import { formatLatency, percent, splitLead } from "../../lib/format.js";
import { AlertIcon, ClockIcon, LayersIcon } from "../icons.jsx";
import RichText from "./RichText.jsx";

function Pill({ children, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-xs ${className}`}>
      {children}
    </span>
  );
}

export default function AnswerView({ question, result }) {
  const cached = result.source === "cache";
  const { lead, rest } = splitLead(result.answer);
  const confidence = percent(result.confidence);

  return (
    <article>
      <h1 className="text-[40px] font-bold leading-[1.15] tracking-tight text-slate-900">{question}</h1>

      {result.insufficient_context ? (
        <div className="mt-8 flex gap-3 rounded-lg border border-amber-200 bg-amber-50 px-6 py-5 text-amber-900">
          <AlertIcon className="mt-1 size-5 shrink-0" />
          <div>
            <p className="font-medium">Your documents don't fully answer this.</p>
            <p className="mt-1 text-sm">The answer below says what is missing instead of guessing.</p>
          </div>
        </div>
      ) : (
        lead && (
          <blockquote className="mt-8 rounded-lg border border-slate-200 bg-slate-50/80 px-6 py-6">
            <p className="border-l-[3px] border-blue-600 pl-6 text-[19px] italic leading-relaxed text-slate-700">“{lead}”</p>
          </blockquote>
        )
      )}

      <div className="mt-7 flex flex-wrap gap-2.5">
        {cached ? (
          <Pill className="border-emerald-200 bg-emerald-50 text-emerald-800">
            <span className="size-2 rounded-full bg-emerald-600" /> Cache Hit
          </Pill>
        ) : (
          <Pill className="border-blue-200 bg-blue-50 text-blue-800">
            <span className="size-2 rounded-full bg-blue-600" /> Generated
          </Pill>
        )}
        <Pill className="border-slate-200 bg-white text-slate-700">
          <ClockIcon className="size-4" /> Response Time: {formatLatency(result.latency_ms)}
        </Pill>
        <Pill className="border-slate-200 bg-white text-slate-700">
          <LayersIcon className="size-4" /> Sources: {result.evidence.length}
        </Pill>
        {confidence != null && (
          <Pill className="border-slate-200 bg-white text-slate-700" title="Retrieval similarity, citation support and completeness combined">
            Confidence: {confidence}%
          </Pill>
        )}
      </div>

      <div className="mt-9">
        <RichText text={result.insufficient_context || !lead ? result.answer : rest} />
      </div>
    </article>
  );
}
