export const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".md", ".txt"];

export function fileKind(filename = "") {
  const ext = filename.split(".").pop().toLowerCase();
  if (ext === "pdf") return "pdf";
  if (ext === "docx" || ext === "doc") return "doc";
  if (["xls", "xlsx", "csv"].includes(ext)) return "sheet";
  return "text";
}

/** "22. Safety Committee and safety officers" -> "Sec 22"; other headings are shortened. */
export function sectionBadge(section) {
  if (!section) return null;
  const m = section.match(/^(\d+[A-Z]?)\./);
  if (m) return `Sec ${m[1]}`;
  return section.length > 14 ? `${section.slice(0, 13)}…` : section;
}

export function formatLatency(ms) {
  if (ms == null) return "–";
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`;
}

export function percent(value) {
  return value == null ? null : Math.round(value * 100);
}

export function timeAgo(iso) {
  if (!iso) return "";
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000;
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
  return new Date(iso).toLocaleDateString();
}

/** Splits an answer into its opening sentence (shown as the lead) and the rest. */
export function splitLead(answer = "") {
  const text = answer.trim();
  const firstBlock = text.split(/\n\s*\n|\n(?=\s*[*-]\s)/)[0];
  const m = firstBlock.match(/^(.+?[.!?])(\s+|$)/s);
  if (!m || firstBlock.trimStart().match(/^[*-]\s/)) return { lead: null, rest: text };
  return { lead: m[1].trim(), rest: text.slice(m[0].length).trim() };
}
