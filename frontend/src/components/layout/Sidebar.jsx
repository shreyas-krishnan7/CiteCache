import { useRef } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";
import { isActive, useDocuments } from "../../context/DocumentsContext.jsx";
import { ACCEPTED_EXTENSIONS } from "../../lib/format.js";
import ProgressBar from "../ProgressBar.jsx";
import { FileIcon, FolderIcon, LogOutIcon, QueryIcon, UploadIcon } from "../icons.jsx";

const RECENT_LIMIT = 6;

function NavItem({ to, icon: IconCmp, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive: active }) =>
        `flex items-center gap-3 rounded-lg px-4 py-3 font-mono text-sm transition-colors ${
          active ? "bg-blue-50 text-blue-700" : "text-slate-700 hover:bg-slate-100"
        }`
      }
    >
      <IconCmp className="size-5 shrink-0" />
      {children}
    </NavLink>
  );
}

function RecentItem({ name, status, progress }) {
  const tone = status === "error" ? "text-red-600" : status === "ready" ? "text-emerald-700" : "text-amber-700";
  const dot = status === "error" ? "bg-red-500" : status === "ready" ? "bg-emerald-600" : "bg-amber-700";
  const label = status === "error" ? "Failed" : status === "ready" ? "Ready" : "Processing";
  return (
    <li className="flex gap-3">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-500">
        <FileIcon className="size-4.5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-mono text-[13px] text-slate-800" title={name}>{name}</p>
        <p className={`mt-0.5 flex items-center gap-1.5 font-mono text-xs ${tone}`}>
          <span className={`size-1.5 rounded-full ${dot}`} />
          {label}
        </p>
        {status === "processing" && <ProgressBar value={progress} tone="warm" className="mt-1.5 h-1" label={`${name} upload`} />}
      </div>
    </li>
  );
}

export default function Sidebar() {
  const { user, signOut } = useAuth();
  const { documents, jobs, upload } = useDocuments();
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const inFlight = jobs.filter((j) => isActive(j) || j.status === "error");
  const recent = [
    ...inFlight.map((j) => ({ key: j.id, name: j.filename, status: j.status === "error" ? "error" : "processing", progress: j.progress })),
    ...documents.map((d) => ({ key: d.source, name: d.filename, status: "ready" })),
  ].slice(0, RECENT_LIMIT);

  const onFiles = (e) => {
    upload(e.target.files);
    e.target.value = "";
    navigate("/documents");
  };

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-slate-200 bg-slate-50/70 md:h-full md:w-80 md:border-b-0 md:border-r">
      <div className="flex items-center gap-3 px-7 pb-6 pt-7">
        <div className="flex size-10 items-center justify-center rounded-lg bg-blue-700 text-lg font-semibold text-white">C</div>
        <div>
          <p className="text-xl font-semibold leading-tight tracking-tight">CiteCache</p>
          <p className="font-mono text-xs text-slate-500">Expert Utility</p>
        </div>
      </div>

      <div className="px-7">
        <input ref={inputRef} type="file" multiple accept={ACCEPTED_EXTENSIONS.join(",")} className="hidden" onChange={onFiles} />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex w-full items-center justify-center gap-2.5 rounded-md bg-blue-700 px-4 py-3 font-mono text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
        >
          <UploadIcon className="size-4.5" />
          Upload Document
        </button>
      </div>

      <nav className="mt-6 space-y-1 px-4">
        <NavItem to="/documents" icon={FolderIcon}>Documents</NavItem>
        <NavItem to="/query" icon={QueryIcon}>Query Workspace</NavItem>
      </nav>

      <div className="mt-7 hidden min-h-0 flex-1 flex-col px-7 md:flex">
        <p className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Recent documents</p>
        {recent.length ? (
          <ul className="mt-4 space-y-5 overflow-y-auto pb-4">
            {recent.map((r) => <RecentItem key={r.key} {...r} />)}
          </ul>
        ) : (
          <p className="mt-4 text-sm text-slate-500">No documents yet.</p>
        )}
      </div>

      <div className="mt-auto flex items-center gap-3 border-t border-slate-200 px-7 py-4">
        <div className="flex size-8 items-center justify-center rounded-full bg-blue-100 font-mono text-sm font-semibold uppercase text-blue-800">
          {user?.username?.[0] ?? "?"}
        </div>
        <p className="min-w-0 flex-1 truncate font-mono text-sm text-slate-700">{user?.username}</p>
        <button
          type="button"
          onClick={signOut}
          className="flex items-center gap-1.5 rounded-md px-2 py-1.5 font-mono text-xs text-slate-500 hover:bg-slate-100 hover:text-slate-800"
          title="Sign out"
        >
          <LogOutIcon className="size-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
