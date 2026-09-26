import { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl bg-white shadow-sm ring-1 ring-slate-100 ${className}`}
    >
      {children}
    </div>
  );
}
