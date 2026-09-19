const TONES = {
  active: "bg-blue-600",
  warm: "bg-amber-700",
  done: "bg-emerald-500",
  error: "bg-red-500",
};

export default function ProgressBar({ value, tone = "active", className = "h-1.5", label }) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  return (
    <div
      className={`w-full overflow-hidden rounded-full bg-slate-200 ${className}`}
      role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label={label}
    >
      <div className={`h-full rounded-full transition-[width] duration-500 ease-out ${TONES[tone]}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
