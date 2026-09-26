import type {
  Call,
  Dashboard,
  Medication,
  Prescription,
  Reminder,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  hint?: string;

  constructor(message: string, status: number, hint?: string) {
    super(message);
    this.status = status;
    this.hint = hint;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        ...(init?.body && !(init.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "We couldn't reach the Dawa Dost server. Please check your connection and try again.",
      0,
    );
  }

  if (!res.ok) {
    let detail: unknown = null;
    try {
      const body = await res.json();
      detail = body?.detail ?? body;
    } catch {
      // ignore non-JSON error bodies
    }
    if (typeof detail === "object" && detail && "message" in detail) {
      const d = detail as { message?: string; hint?: string };
      throw new ApiError(d.message || "Something went wrong.", res.status, d.hint);
    }
    if (typeof detail === "string") {
      throw new ApiError(detail, res.status);
    }
    throw new ApiError("Something went wrong. Please try again.", res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  getDashboard: () => request<Dashboard>("/api/dashboard"),
  getProgress: () => request<{ adherence_percent: number; symptom_trends: unknown[] }>("/api/progress"),

  listPrescriptions: () => request<Prescription[]>("/api/prescriptions"),
  getPrescription: (id: string) => request<Prescription>(`/api/prescriptions/${id}`),
  uploadPrescription: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Prescription>("/api/prescriptions/upload", {
      method: "POST",
      body: form,
    });
  },
  extractPrescription: (id: string) =>
    request<Prescription>(`/api/prescriptions/${id}/extract`, { method: "POST" }),
  confirmPrescription: (
    id: string,
    medications: Array<{
      medicine_name: string;
      strength?: string | null;
      dose?: string | null;
      frequency?: string | null;
      duration?: string | null;
      food_instruction?: string | null;
      special_instruction?: string | null;
    }>,
  ) =>
    request<Medication[]>(`/api/prescriptions/${id}/confirm`, {
      method: "POST",
      body: JSON.stringify({ medications }),
    }),

  listMedications: () => request<Medication[]>("/api/medications"),
  getMedication: (id: string) => request<Medication>(`/api/medications/${id}`),
  getMedicationReminders: (id: string) =>
    request<Reminder[]>(`/api/medications/${id}/reminders`),
  getMedicationAdherence: (id: string) =>
    request<{
      medication_id: string;
      adherence_percent: number;
      total_reminders: number;
      taken: number;
      events: Array<{ id: string; status: string; scheduled_at: string; reported_at: string; reason: string | null }>;
    }>(`/api/medications/${id}/adherence`),

  listCalls: () => request<Call[]>("/api/calls"),

  triggerCall: (reminderId: string) =>
    request<{ status: string; interaction_id: string }>("/api/voice/trigger", {
      method: "POST",
      body: JSON.stringify({ reminder_id: reminderId }),
    }),

  simulateOutcome: (
    reminderId: string,
    outcome: Record<string, unknown> = { medication_taken: true },
  ) =>
    request<{ status: string; call_id: string }>("/api/demo/simulate-outcome", {
      method: "POST",
      body: JSON.stringify({ reminder_id: reminderId, outcome }),
    }),

  fileUrl: (path: string) => `${API_URL}${path}`,
};
