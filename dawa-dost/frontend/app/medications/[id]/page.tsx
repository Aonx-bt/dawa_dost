"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { ErrorState, LoadingState } from "@/components/States";
import { StatusBadge, ReviewBadge } from "@/components/Badge";
import type { Medication, Reminder } from "@/types";

interface AdherenceSummary {
  adherence_percent: number;
  total_reminders: number;
  taken: number;
}

export default function MedicationDetailPage() {
  const params = useParams<{ id: string }>();
  const [medication, setMedication] = useState<Medication | null>(null);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [adherence, setAdherence] = useState<AdherenceSummary | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [callingId, setCallingId] = useState<string | null>(null);

  const load = () => {
    setError(null);
    Promise.all([
      api.getMedication(params.id),
      api.getMedicationReminders(params.id),
      api.getMedicationAdherence(params.id),
    ])
      .then(([med, rem, adh]) => {
        setMedication(med);
        setReminders(rem);
        setAdherence(adh);
      })
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  };

  useEffect(load, [params.id]);

  const handleSimulateCall = async (reminderId: string) => {
    setCallingId(reminderId);
    try {
      await api.simulateOutcome(reminderId, { medication_taken: true });
      load();
    } finally {
      setCallingId(null);
    }
  };

  if (error) return <div className="p-4"><ErrorState description={error.message} onRetry={load} /></div>;
  if (!medication) return <LoadingState label="Loading medication..." />;

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="pt-2">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold text-slate-900">{medication.name}</h1>
          {medication.needs_review && <ReviewBadge />}
        </div>
        <p className="text-sm text-slate-500">
          {[medication.strength, medication.dose].filter(Boolean).join(" · ")}
        </p>
      </div>

      <Card className="p-4 text-sm text-slate-600">
        <div className="grid grid-cols-2 gap-y-2">
          <span className="text-slate-400">Frequency</span>
          <span>{medication.is_sos ? "As needed (SOS)" : medication.frequency}</span>
          <span className="text-slate-400">Duration</span>
          <span>{medication.duration || "—"}</span>
          <span className="text-slate-400">Food instruction</span>
          <span>{medication.food_instruction || "—"}</span>
          <span className="text-slate-400">Special instruction</span>
          <span>{medication.special_instruction || "—"}</span>
        </div>
      </Card>

      {adherence && (
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Adherence</p>
            <p className="text-lg font-semibold text-slate-900">
              {adherence.taken} / {adherence.total_reminders} taken
            </p>
          </div>
          <div className="text-2xl font-bold text-teal-700">{adherence.adherence_percent}%</div>
        </Card>
      )}

      <section>
        <h2 className="mb-2 px-1 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Reminders
        </h2>
        <Card className="divide-y divide-slate-100">
          {reminders.map((r) => (
            <div key={r.id} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-medium text-slate-800">
                  {new Date(r.scheduled_at).toLocaleString([], {
                    weekday: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={r.status} />
                {(r.status === "PENDING" || r.status === "TRIGGERED") && (
                  <button
                    onClick={() => handleSimulateCall(r.id)}
                    disabled={callingId === r.id}
                    className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 disabled:opacity-50"
                  >
                    {callingId === r.id ? "..." : "Mark taken (demo)"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </Card>
      </section>
    </div>
  );
}
