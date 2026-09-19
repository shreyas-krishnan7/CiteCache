// Outline icons (24x24, stroke = currentColor) -- inline so no icon library is needed.
function Icon({ className = "size-5", children, ...rest }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
         strokeLinejoin="round" className={className} aria-hidden="true" {...rest}>
      {children}
    </svg>
  );
}

export const SearchIcon = (p) => (
  <Icon {...p}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.8-3.8" /></Icon>
);
export const UploadIcon = (p) => (
  <Icon {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="M17 8l-5-5-5 5" /><path d="M12 3v12" /></Icon>
);
export const FileIcon = (p) => (
  <Icon {...p}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /></Icon>
);
export const FileTextIcon = (p) => (
  <Icon {...p}>
    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" />
    <path d="M9 13h6" /><path d="M9 17h6" />
  </Icon>
);
export const PdfIcon = (p) => (
  <Icon {...p}>
    <rect x="4" y="3" width="16" height="18" rx="2" /><path d="M8 3v18" />
    <path d="M11 9h5" /><path d="M11 13h5" />
  </Icon>
);
export const SheetIcon = (p) => (
  <Icon {...p}><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M3 15h18M9 9v12M15 9v12" /></Icon>
);
export const FolderIcon = (p) => (
  <Icon {...p}><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.7-.9l-.8-1.2A2 2 0 0 0 7.9 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" /></Icon>
);
export const QueryIcon = (p) => (
  <Icon {...p}><circle cx="10.5" cy="10.5" r="6.5" /><path d="m20 20-4.4-4.4" /><path d="M8 10.5h5M10.5 8v5" /></Icon>
);
export const ArrowRightIcon = (p) => (
  <Icon {...p}><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></Icon>
);
export const ClockIcon = (p) => (
  <Icon {...p}><circle cx="12" cy="13" r="8" /><path d="M12 9v4l2.5 1.5" /><path d="M10 2h4" /></Icon>
);
export const LayersIcon = (p) => (
  <Icon {...p}><rect x="8" y="8" width="13" height="13" rx="2" /><path d="M4 16a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2" /></Icon>
);
export const BadgeCheckIcon = (p) => (
  <Icon {...p}>
    <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" />
    <path d="m9 12 2 2 4-4" />
  </Icon>
);
export const CheckIcon = (p) => (
  <Icon {...p}><path d="M20 6 9 17l-5-5" /></Icon>
);
export const AlertIcon = (p) => (
  <Icon {...p}><path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></Icon>
);
export const ChevronDownIcon = (p) => (
  <Icon {...p}><path d="m6 9 6 6 6-6" /></Icon>
);
export const FlowIcon = (p) => (
  <Icon {...p}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /><path d="M6.5 10v3a2 2 0 0 0 2 2H14" /></Icon>
);
export const LogOutIcon = (p) => (
  <Icon {...p}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5" /><path d="M21 12H9" /></Icon>
);
export const XIcon = (p) => (
  <Icon {...p}><path d="M18 6 6 18" /><path d="m6 6 12 12" /></Icon>
);
export const Spinner = ({ className = "size-5" }) => (
  <svg viewBox="0 0 24 24" fill="none" className={`animate-spin ${className}`} aria-hidden="true">
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.2" strokeWidth="2.5" />
    <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);

export function DocTypeIcon({ filename, className }) {
  const ext = (filename || "").split(".").pop().toLowerCase();
  if (ext === "pdf") return <PdfIcon className={className} />;
  if (["xls", "xlsx", "csv"].includes(ext)) return <SheetIcon className={className} />;
  if (ext === "docx" || ext === "doc") return <FileTextIcon className={className} />;
  return <FileIcon className={className} />;
}
