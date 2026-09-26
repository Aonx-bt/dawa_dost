export interface User {
  id: string;
  name: string;
  phone: string;
  preferred_language: string;
  created_at: string;
}

export interface ExtractedMedication {
  medicine_name: string;
  strength?: string | null;
  dose?: string | null;
  frequency?: string | null;
  duration?: string | null;
  food_instruction?: string | null;
  special_instruction?: string | null;
  needs_review?: boolean;
}

export interface RawExtraction {
  patient_name?: string | null;
  doctor_name?: string | null;
  diagnoses: string[];
  symptoms: string[];
  medications: ExtractedMedication[];
}

export interface Prescription {
  id: string;
  user_id: string;
  image_url: string | null;
  doctor_name: string | null;
  diagnoses: string[];
  symptoms: string[];
  raw_extraction: RawExtraction | null;
  status: "UPLOADED" | "PROCESSING" | "EXTRACTED" | "FAILED" | "CONFIRMED";
  created_at: string;
}

export interface Medication {
  id: string;
  user_id: string;
  prescription_id: string | null;
  name: string;
  strength: string | null;
  dose: string | null;
  frequency: string | null;
  frequency_code: string | null;
  times: string[];
  duration: string | null;
  start_date: string | null;
  end_date: string | null;
  food_instruction: string | null;
  special_instruction: string | null;
  is_sos: boolean;
  needs_review: boolean;
  confirmed: boolean;
  created_at: string;
}

export type ReminderStatus =
  | "PENDING"
  | "TRIGGERED"
  | "COMPLETED"
  | "MISSED"
  | "SNOOZED"
  | "CANCELLED";

export interface Reminder {
  id: string;
  user_id: string;
  medication_id: string;
  scheduled_at: string;
  status: ReminderStatus;
  call_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Call {
  id: string;
  user_id: string;
  reminder_id: string | null;
  sarvam_interaction_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  duration: number | null;
  transcript: string | null;
  outcome: Record<string, unknown> | null;
  created_at: string;
}

export interface TodayDose {
  reminder_id: string;
  medication_name: string;
  dose: string | null;
  scheduled_at: string;
  status: ReminderStatus;
}

export interface SymptomTrendPoint {
  reported_at: string;
  severity: number | null;
  trend: string | null;
}

export interface SymptomTrend {
  symptom: string;
  source: string;
  points: SymptomTrendPoint[];
}

export interface Dashboard {
  user: User;
  adherence_percent: number;
  doses_completed_today: number;
  doses_total_today: number;
  today: TodayDose[];
  symptom_trends: SymptomTrend[];
  recent_calls: Call[];
}

export interface ApiErrorDetail {
  message?: string;
  hint?: string;
  reason?: string;
}
