const STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-slate-100 text-slate-600",
  TRIGGERED: "bg-amber-100 text-amber-700",
  COMPLETED: "bg-emerald-100 text-emerald-700",
  MISSED: "bg-rose-100 text-rose-700",
  SNOOZED: "bg-sky-100 text-sky-700",
  CANCELLED: "bg-slate-100 text-slate-400",
  TAKEN: "bg-emerald-100 text-emerald-700",
  REFUSED: "bg-rose-100 text-rose-700",
  UNKNOWN: "bg-slate-100 text-slate-500",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${style}`}>
      {status.charAt(0) + status.slice(1).toLowerCase()}
    </span>
  );
}

export function ReviewBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800">
      ⚠ Please verify
    </span>
  );
}

export function SourceBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-teal-50 px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide text-teal-700">
      {label}
    </span>
  );
}
