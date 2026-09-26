import { ReactNode } from "react";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-200 border-t-teal-600" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-2xl bg-white px-6 py-12 text-center ring-1 ring-slate-100">
      {icon && <div className="mb-1 text-4xl">{icon}</div>}
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      {description && (
        <p className="max-w-xs text-sm text-slate-500">{description}</p>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  hint,
  onRetry,
}: {
  title?: string;
  description?: string;
  hint?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl bg-rose-50 px-6 py-10 text-center ring-1 ring-rose-100">
      <div className="text-3xl">⚠️</div>
      <h3 className="text-base font-semibold text-rose-800">{title}</h3>
      {description && <p className="max-w-sm text-sm text-rose-700">{description}</p>}
      {hint && <p className="max-w-sm text-sm text-rose-500">{hint}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-full bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700"
        >
          Try again
        </button>
      )}
    </div>
  );
}
