"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MedicineInsightsResponse } from "@/types";

export function useMedicineInsights(medicineNames: string[]) {
  const [insights, setInsights] = useState<MedicineInsightsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const names = medicineNames.filter((n) => n && n.trim());
    if (names.length === 0) {
      setInsights(null);
      return;
    }
    setLoading(true);
    api
      .getMedicineInsights(names)
      .then(setInsights)
      .catch(() => setInsights(null))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(medicineNames)]);

  return { insights, loading };
}
