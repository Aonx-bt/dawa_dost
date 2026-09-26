"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { ErrorState, LoadingState } from "@/components/States";
import type { Dashboard } from "@/types";

export default function ProfilePage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    api
      .getDashboard()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  }, []);

  if (error) return <div className="p-4"><ErrorState description={error.message} /></div>;
  if (!data) return <LoadingState label="Loading profile..." />;

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="pt-2 text-xl font-semibold text-slate-900">Profile</h1>

      <Card className="flex items-center gap-4 p-5">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-teal-100 text-xl font-semibold text-teal-700">
          {data.user.name.charAt(0)}
        </div>
        <div>
          <p className="text-base font-semibold text-slate-900">{data.user.name}</p>
          <p className="text-sm text-slate-500">{data.user.phone}</p>
        </div>
      </Card>

      <Card className="p-4 text-sm text-slate-600">
        <div className="flex items-center justify-between py-2">
          <span className="text-slate-400">Preferred language</span>
          <span>{data.user.preferred_language}</span>
        </div>
        <div className="flex items-center justify-between border-t border-slate-100 py-2">
          <span className="text-slate-400">Patient since</span>
          <span>{new Date(data.user.created_at).toLocaleDateString()}</span>
        </div>
      </Card>

      <Card className="p-4 text-xs leading-relaxed text-slate-500">
        Dawa Dost is a medication-adherence companion. It does not diagnose conditions,
        change dosages, or recommend medication changes. Always consult your doctor for
        medical decisions.
      </Card>
    </div>
  );
}
