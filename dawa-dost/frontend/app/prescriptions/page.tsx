"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { StatusBadge } from "@/components/Badge";
import type { Prescription } from "@/types";

export default function PrescriptionsPage() {
  const [items, setItems] = useState<Prescription[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const load = () => {
    setError(null);
    api
      .listPrescriptions()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  };

  useEffect(load, []);

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center justify-between pt-2">
        <h1 className="text-xl font-semibold text-slate-900">Prescriptions</h1>
        <Link
          href="/prescriptions/upload"
          className="rounded-full bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
        >
          + Upload
        </Link>
      </div>

      {error && <ErrorState description={error.message} onRetry={load} />}

      {!items && !error && <LoadingState label="Loading prescriptions..." />}

      {items && items.length === 0 && (
        <EmptyState
          icon="📄"
          title="No prescriptions yet"
          description="Upload your first prescription to get started."
          action={
            <Link
              href="/prescriptions/upload"
              className="rounded-full bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
            >
              Upload Prescription
            </Link>
          }
        />
      )}

      {items && items.length > 0 && (
        <Card className="divide-y divide-slate-100">
          {items.map((p) => (
            <Link
              key={p.id}
              href={`/prescriptions/${p.id}`}
              className="flex items-center justify-between p-4 hover:bg-slate-50"
            >
              <div>
                <p className="font-medium text-slate-800">
                  {p.doctor_name || "Prescription"}
                </p>
                <p className="text-xs text-slate-400">
                  {new Date(p.created_at).toLocaleDateString()}
                </p>
              </div>
              <StatusBadge status={p.status} />
            </Link>
          ))}
        </Card>
      )}
    </div>
  );
}
