"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import type { Call } from "@/types";

export default function CallsPage() {
  const [items, setItems] = useState<Call[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const load = () => {
    setError(null);
    api
      .listCalls()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  };

  useEffect(load, []);

  if (error) return <div className="p-4"><ErrorState description={error.message} onRetry={load} /></div>;
  if (!items) return <LoadingState label="Loading call history..." />;

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="pt-2 text-xl font-semibold text-slate-900">Call History</h1>

      {items.length === 0 ? (
        <EmptyState
          icon="📞"
          title="No calls yet"
          description="Once Dawa Dost calls you for a reminder, the conversation will show up here."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((call) => {
            const outcome = call.outcome as Record<string, unknown> | null;
            return (
              <Card key={call.id} className="p-4">
                <div className="mb-1 flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-800">
                    {call.started_at ? new Date(call.started_at).toLocaleString() : "Unknown time"}
                  </p>
                  {call.duration != null && (
                    <span className="text-xs text-slate-400">{call.duration}s</span>
                  )}
                </div>
                {call.transcript && (
                  <p className="mb-2 rounded-lg bg-slate-50 p-2 text-xs text-slate-500">
                    &ldquo;{call.transcript}&rdquo;
                  </p>
                )}
                <div className="flex flex-wrap gap-2 text-xs">
                  {outcome?.medication_taken ? (
                    <span className="rounded-full bg-emerald-100 px-2 py-1 font-medium text-emerald-700">
                      Medication taken
                    </span>
                  ) : null}
                  {outcome?.snooze_requested ? (
                    <span className="rounded-full bg-sky-100 px-2 py-1 font-medium text-sky-700">
                      Snoozed
                    </span>
                  ) : null}
                  {outcome?.symptom_reported ? (
                    <span className="rounded-full bg-amber-100 px-2 py-1 font-medium text-amber-700">
                      Symptom: {String(outcome?.symptom_name ?? "")}
                    </span>
                  ) : null}
                  {outcome?.side_effect_reported ? (
                    <span className="rounded-full bg-rose-100 px-2 py-1 font-medium text-rose-700">
                      Side effect reported
                    </span>
                  ) : null}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
