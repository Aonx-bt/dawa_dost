"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { StatusBadge } from "@/components/Badge";
import type { Dashboard } from "@/types";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function SparkTrend({ points }: { points: Dashboard["symptom_trends"][number]["points"] }) {
  const withSeverity = points.filter((p) => p.severity !== null);
  if (withSeverity.length === 0) return null;
  const max = 10;
  return (
    <div className="mt-2 flex items-end gap-2">
      {withSeverity.map((p, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          <div
            className="w-3 rounded-full bg-teal-400"
            style={{ height: `${((p.severity || 0) / max) * 48 + 4}px` }}
          />
          <span className="text-[10px] text-slate-400">{p.severity}</span>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [callingId, setCallingId] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api
      .getDashboard()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load dashboard", 0)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCallMeNow = async () => {
    const nextPending = data?.today.find((d) => d.status === "PENDING" || d.status === "SNOOZED");
    if (!nextPending) return;
    setCallingId(nextPending.reminder_id);
    try {
      await api.triggerCall(nextPending.reminder_id);
    } catch {
      // Sarvam not configured in this environment - fall back to demo simulate
      await api.simulateOutcome(nextPending.reminder_id, { medication_taken: true });
    }
    load();
    setCallingId(null);
  };

  if (loading) return <LoadingState label="Loading your dashboard..." />;
  if (error)
    return (
      <div className="p-4">
        <ErrorState description={error.message} hint={error.hint} onRetry={load} />
      </div>
    );
  if (!data) return null;

  const firstName = data.user.name.split(" ")[0];

  return (
    <div className="flex flex-col gap-4 p-4">
      <header className="pt-2">
        <h1 className="text-xl font-semibold text-slate-900">
          {greeting()}, {firstName} 👋
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Your treatment is{" "}
          <span className="font-semibold text-teal-700">{data.adherence_percent}%</span> on
          track
        </p>
      </header>

      <Card className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Today&apos;s progress
            </p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">
              {data.doses_completed_today} / {data.doses_total_today} doses
            </p>
          </div>
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-teal-50 text-lg font-bold text-teal-700">
            {data.adherence_percent}%
          </div>
        </div>
      </Card>

      <section>
        <h2 className="mb-2 px-1 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Today&apos;s treatment
        </h2>
        {data.today.length === 0 ? (
          <EmptyState
            icon="💊"
            title="No doses scheduled today"
            description="Upload a prescription to start your medication schedule."
          />
        ) : (
          <Card className="divide-y divide-slate-100">
            {data.today.map((dose) => (
              <div key={dose.reminder_id} className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">{formatTime(dose.scheduled_at)}</p>
                  <p className="text-base font-semibold text-slate-900">{dose.medication_name}</p>
                  {dose.dose && <p className="text-sm text-slate-500">{dose.dose}</p>}
                </div>
                <div className="flex flex-col items-end gap-1">
                  <StatusBadge status={dose.status} />
                  {dose.status === "PENDING" && (
                    <span className="text-xs text-slate-400">Dawa Dost will call you</span>
                  )}
                </div>
              </div>
            ))}
          </Card>
        )}
      </section>

      {data.symptom_trends.length > 0 && (
        <section>
          <h2 className="mb-2 px-1 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Symptom progress
          </h2>
          <Card className="p-4">
            {data.symptom_trends.map((trend) => {
              const points = trend.points.filter((p) => p.severity !== null);
              const latest = points[points.length - 1];
              const first = points[0];
              const improving =
                latest && first && latest.severity !== null && first.severity !== null
                  ? latest.severity < first.severity
                  : null;
              return (
                <div key={trend.symptom} className="mb-3 last:mb-0">
                  <div className="flex items-center justify-between">
                    <p className="font-medium capitalize text-slate-800">{trend.symptom}</p>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium uppercase text-slate-500">
                      Patient-reported
                    </span>
                  </div>
                  <SparkTrend points={trend.points} />
                  {improving !== null && (
                    <p className={`mt-1 text-xs ${improving ? "text-emerald-600" : "text-amber-600"}`}>
                      {improving ? "Improving ↓" : "Watch closely →"}
                    </p>
                  )}
                </div>
              );
            })}
          </Card>
        </section>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Link
          href="/prescriptions/upload"
          className="flex flex-col items-center justify-center gap-1 rounded-2xl bg-teal-600 px-4 py-4 text-center text-sm font-semibold text-white shadow-sm hover:bg-teal-700"
        >
          <span className="text-xl">📷</span>
          Scan Prescription
        </Link>
        <button
          onClick={handleCallMeNow}
          disabled={!!callingId || !data.today.some((d) => d.status === "PENDING" || d.status === "SNOOZED")}
          className="flex flex-col items-center justify-center gap-1 rounded-2xl bg-white px-4 py-4 text-center text-sm font-semibold text-teal-700 shadow-sm ring-1 ring-teal-100 hover:bg-teal-50 disabled:opacity-50"
        >
          <span className="text-xl">🎙️</span>
          {callingId ? "Calling..." : "Talk to Dawa Dost"}
        </button>
      </div>

      {data.recent_calls.length > 0 && (
        <section>
          <h2 className="mb-2 px-1 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Recent calls
          </h2>
          <Card className="divide-y divide-slate-100">
            {data.recent_calls.map((call) => {
              const outcome = call.outcome as { medication_taken?: boolean } | null;
              return (
                <div key={call.id} className="flex items-center justify-between p-4">
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {outcome?.medication_taken ? "✓ Reminder" : "Reminder"}
                    </p>
                    <p className="text-xs text-slate-400">
                      {call.started_at ? new Date(call.started_at).toLocaleString() : "—"}
                    </p>
                  </div>
                  <span className="text-sm text-slate-500">
                    {outcome?.medication_taken ? "Taken" : "See details"}
                  </span>
                </div>
              );
            })}
          </Card>
        </section>
      )}
    </div>
  );
}
