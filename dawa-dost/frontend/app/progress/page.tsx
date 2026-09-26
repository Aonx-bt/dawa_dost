"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { ErrorState, LoadingState, EmptyState } from "@/components/States";
import type { Dashboard } from "@/types";

export default function ProgressPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const load = () => {
    setError(null);
    api
      .getDashboard()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  };

  useEffect(load, []);

  if (error) return <div className="p-4"><ErrorState description={error.message} onRetry={load} /></div>;
  if (!data) return <LoadingState label="Loading progress..." />;

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="pt-2 text-xl font-semibold text-slate-900">Your Progress</h1>

      <Card className="p-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Medication adherence
        </p>
        <p className="mt-1 text-3xl font-bold text-teal-700">{data.adherence_percent}%</p>
        <p className="text-sm text-slate-500">taken doses / scheduled doses</p>
      </Card>

      <section>
        <h2 className="mb-2 px-1 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Symptom trends
        </h2>
        {data.symptom_trends.length === 0 ? (
          <EmptyState
            icon="📈"
            title="No symptoms reported yet"
            description="Symptoms reported during your calls with Dawa Dost will appear here."
          />
        ) : (
          <div className="flex flex-col gap-3">
            {data.symptom_trends.map((trend) => (
              <Card key={trend.symptom} className="p-4">
                <div className="mb-2 flex items-center justify-between">
                  <p className="font-medium capitalize text-slate-800">{trend.symptom}</p>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium uppercase text-slate-500">
                    Patient-reported
                  </span>
                </div>
                <div className="flex flex-col gap-1 text-sm">
                  {trend.points.map((p, i) => (
                    <div key={i} className="flex items-center justify-between text-slate-600">
                      <span>Day {i + 1}</span>
                      <span>
                        {p.severity !== null ? `${p.severity}/10` : "—"}
                        {p.trend && p.trend !== "unknown" ? ` · ${p.trend}` : ""}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}
        <p className="mt-2 px-1 text-xs text-slate-400">
          This reflects what you told Dawa Dost during calls - not a medical diagnosis.
        </p>
      </section>
    </div>
  );
}
