import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { isActive, useDocuments } from "../../context/DocumentsContext.jsx";
import { ACCEPTED_EXTENSIONS, timeAgo } from "../../lib/format.js";
import ProgressBar from "../ProgressBar.jsx";
import { AlertIcon, ArrowRightIcon, CheckIcon, DocTypeIcon, Spinner, UploadIcon, XIcon } from "../icons.jsx";

function stageDetail(job) {
  if (job.status === "queued") return "Waiting for the current upload to finish";
  if (job.status === "error") return job.error || "Upload failed";
  if (job.status === "done") return `Indexed ${job.chunks_total} chunk${job.chunks_total === 1 ? "" : "s"}`;
  if (job.chunks_total) return `${job.stage} · ${job.chunks_done}/${job.chunks_total} chunks`;
  return job.stage;
}

function JobCard({ job }) {
  const tone = job.status === "error" ? "error" : job.status === "done" ? "done" : "active";
  return (
    <li className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
      <div className="flex items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-500">
          <DocTypeIcon filename={job.filename} className="size-4.5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p className="truncate font-mono text-sm text-slate-800" title={job.filename}>{job.filename}</p>
            <span className="shrink-0 font-mono text-xs tabular-nums text-slate-500">
              {job.status === "error" ? "" : `${job.progress}%`}
            </span>
          </div>
          <p className={`mt-1 flex items-center gap-1.5 text-xs ${job.status === "error" ? "text-red-700" : "text-slate-500"}`}>
            {isActive(job) && <Spinner className="size-3" />}
            {job.status === "done" && <CheckIcon className="size-3.5 text-emerald-600" />}
            {job.status === "error" && <AlertIcon className="size-3.5" />}
            {stageDetail(job)}
          </p>
          <ProgressBar value={job.status === "error" ? 100 : job.progress} tone={tone} className="mt-3 h-1.5" label={`${job.filename} progress`} />
        </div>
      </div>
    </li>
  );
}

export default function DocumentUpload() {
  const { documents, jobs, loaded, upload, uploadError, clearUploadError } = useDocuments();
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const totalChunks = documents.reduce((n, d) => n + d.chunks, 0);

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    upload(e.dataTransfer.files);
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-6 py-10 lg:px-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
            <p className="mt-1.5 text-slate-500">
              Upload files to your private workspace. Each one is split into chunks, embedded and indexed for search.
            </p>
          </div>
          {documents.length > 0 && (
            <Link
              to="/query"
              className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2.5 font-mono text-sm text-slate-800 shadow-xs transition hover:border-blue-300 hover:text-blue-700"
            >
              Ask a question <ArrowRightIcon className="size-4" />
            </Link>
          )}
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`mt-8 flex flex-col items-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
            dragging ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-slate-50/60"
          }`}
        >
          <div className="flex size-12 items-center justify-center rounded-full bg-blue-50 text-blue-700">
            <UploadIcon className="size-6" />
          </div>
          <p className="mt-4 text-base font-medium">Drag and drop files here</p>
          <p className="mt-1 text-sm text-slate-500">
            or{" "}
            <button type="button" onClick={() => inputRef.current?.click()} className="font-medium text-blue-700 hover:underline">
              browse your computer
            </button>
          </p>
          <p className="mt-3 font-mono text-xs text-slate-400">PDF · DOCX · MD · TXT — up to 25 MB each</p>
          <input
            ref={inputRef} type="file" multiple accept={ACCEPTED_EXTENSIONS.join(",")} className="hidden"
            onChange={(e) => { upload(e.target.files); e.target.value = ""; }}
          />
        </div>

        {uploadError && (
          <div role="alert" className="mt-4 flex items-start gap-2.5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertIcon className="mt-0.5 size-4 shrink-0" />
            <span className="flex-1">{uploadError}</span>
            <button type="button" onClick={clearUploadError} aria-label="Dismiss" className="text-red-500 hover:text-red-800">
              <XIcon className="size-4" />
            </button>
          </div>
        )}

        {jobs.length > 0 && (
          <section className="mt-10">
            <h2 className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Uploads</h2>
            <ul className="mt-4 space-y-3">
              {jobs.map((job) => <JobCard key={job.id} job={job} />)}
            </ul>
          </section>
        )}

        <section className="mt-10">
          <div className="flex items-baseline justify-between">
            <h2 className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Your documents</h2>
            {documents.length > 0 && (
              <p className="font-mono text-xs text-slate-400">{documents.length} files · {totalChunks} chunks</p>
            )}
          </div>
          {!loaded ? (
            <div className="mt-6 flex justify-center text-slate-400"><Spinner /></div>
          ) : documents.length === 0 ? (
            <p className="mt-4 rounded-lg border border-slate-200 px-5 py-8 text-center text-sm text-slate-500">
              Nothing indexed yet. Upload a document to get started.
            </p>
          ) : (
            <ul className="mt-4 divide-y divide-slate-200 rounded-lg border border-slate-200">
              {documents.map((d) => (
                <li key={d.source} className="flex items-center gap-4 px-5 py-4">
                  <DocTypeIcon filename={d.filename} className="size-5 shrink-0 text-slate-500" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-mono text-sm text-slate-800" title={d.filename}>{d.filename}</p>
                    <p className="mt-0.5 text-xs text-slate-500">{d.chunks} chunks · uploaded {timeAgo(d.uploaded_at)}</p>
                  </div>
                  <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 font-mono text-xs text-emerald-700">
                    <span className="size-1.5 rounded-full bg-emerald-600" /> Ready
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
