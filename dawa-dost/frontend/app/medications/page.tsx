"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { ReviewBadge } from "@/components/Badge";
import type { Medication } from "@/types";

export default function MedicationsPage() {
  const [items, setItems] = useState<Medication[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const load = () => {
    setError(null);
    api
      .listMedications()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  };

  useEffect(load, []);

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="pt-2 text-xl font-semibold text-slate-900">My Medications</h1>

      {error && <ErrorState description={error.message} onRetry={load} />}
      {!items && !error && <LoadingState label="Loading medications..." />}

      {items && items.length === 0 && (
        <EmptyState
          icon="💊"
          title="No medications yet"
          description="Confirm a scanned prescription to start tracking medications here."
          action={
            <Link
              href="/prescriptions/upload"
              className="rounded-full bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
            >
              Scan Prescription
            </Link>
          }
        />
      )}

      {items && items.length > 0 && (
        <div className="flex flex-col gap-3">
          {items.map((m) => (
            <Link key={m.id} href={`/medications/${m.id}`}>
              <Card className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-base font-semibold text-slate-900">{m.name}</p>
                    <p className="text-sm text-slate-500">
                      {[m.strength, m.dose].filter(Boolean).join(" · ")}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {m.is_sos ? "As needed (SOS)" : m.times.join(", ") || m.frequency}
                    </p>
                  </div>
                  {m.needs_review && <ReviewBadge />}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
