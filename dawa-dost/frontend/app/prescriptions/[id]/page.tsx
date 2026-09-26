"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { ErrorState, LoadingState } from "@/components/States";
import { ReviewBadge } from "@/components/Badge";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useTranslatedTexts } from "@/hooks/useTranslatedTexts";
import type { ExtractedMedication, Prescription } from "@/types";

const AMBIGUOUS_CODES = new Set(["sos", "prn", "bd", "tds", "qds", "stat"]);

function needsReview(med: ExtractedMedication): boolean {
  if (med.needs_review) return true;
  const freq = (med.frequency || "").trim().toLowerCase();
  if (!freq) return true;
  if (AMBIGUOUS_CODES.has(freq) && freq !== "sos" && freq !== "prn") return true;
  return false;
}

export default function PrescriptionDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [meds, setMeds] = useState<ExtractedMedication[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    setError(null);
    api
      .getPrescription(params.id)
      .then((p) => {
        setPrescription(p);
        setMeds(p.raw_extraction?.medications ?? []);
      })
      .catch((e) => setError(e instanceof ApiError ? e : new ApiError("Failed to load", 0)));
  };

  useEffect(load, [params.id]);

  const updateMed = (index: number, patch: Partial<ExtractedMedication>) => {
    setMeds((prev) => prev.map((m, i) => (i === index ? { ...m, ...patch } : m)));
  };

  const handleConfirm = async () => {
    if (!prescription) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.confirmPrescription(
        prescription.id,
        meds.map((m) => ({
          medicine_name: m.medicine_name,
          strength: m.strength,
          dose: m.dose,
          frequency: m.frequency,
          duration: m.duration,
          food_instruction: m.food_instruction,
          special_instruction: m.special_instruction,
        })),
      );
      router.push("/medications");
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError("Could not confirm prescription.", 0));
    } finally {
      setSubmitting(false);
    }
  };

  if (error) return <div className="p-4"><ErrorState description={error.message} hint={error.hint} onRetry={load} /></div>;
  if (!prescription) return <LoadingState label="Loading prescription..." />;

  if (prescription.status === "PROCESSING" || prescription.status === "UPLOADED") {
    return (
      <div className="p-4">
        <LoadingState label="Still processing this prescription..." />
      </div>
    );
  }

  if (prescription.status === "FAILED") {
    return (
      <div className="p-4">
        <ErrorState
          title="We couldn't read this prescription clearly."
          description="Please upload a clearer photo or enter the medicine details manually."
        />
      </div>
    );
  }

  if (prescription.status === "CONFIRMED") {
    return (
      <div className="flex flex-col gap-4 p-4">
        <h1 className="pt-2 text-xl font-semibold text-slate-900">Prescription confirmed ✓</h1>
        <Card className="p-5 text-sm text-slate-600">
          This prescription has already been confirmed and its medication schedule is active.
        </Card>
        <Link
          href="/medications"
          className="rounded-full bg-teal-600 px-4 py-3 text-center text-sm font-semibold text-white hover:bg-teal-700"
        >
          View my medications
        </Link>
      </div>
    );
  }

  return (
    <PrescriptionReview
      prescription={prescription}
      meds={meds}
      editingIndex={editingIndex}
      setEditingIndex={setEditingIndex}
      updateMed={updateMed}
      handleConfirm={handleConfirm}
      submitting={submitting}
    />
  );
}

function PrescriptionReview({
  prescription,
  meds,
  editingIndex,
  setEditingIndex,
  updateMed,
  handleConfirm,
  submitting,
}: {
  prescription: Prescription;
  meds: ExtractedMedication[];
  editingIndex: number | null;
  setEditingIndex: (i: number | null) => void;
  updateMed: (index: number, patch: Partial<ExtractedMedication>) => void;
  handleConfirm: () => void;
  submitting: boolean;
}) {
  // Translation is display-only: the underlying `meds` state (sent to the
  // backend on confirm, and shown in the edit form) always stays in the
  // originally extracted language so nothing gets lost or mis-parsed.
  const { translated: translatedNames } = useTranslatedTexts(meds.map((m) => m.medicine_name));
  const { translated: translatedDoses } = useTranslatedTexts(meds.map((m) => m.dose || ""));
  const { translated: translatedDurations } = useTranslatedTexts(meds.map((m) => m.duration || ""));
  const { translated: translatedFoodInstructions } = useTranslatedTexts(
    meds.map((m) => m.food_instruction || ""),
  );
  const { translated: translatedDiagnoses } = useTranslatedTexts(prescription.diagnoses);
  const { translated: translatedSymptoms } = useTranslatedTexts(prescription.symptoms);

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-start justify-between pt-2">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Prescription scanned ✓</h1>
          <p className="mt-1 text-sm text-slate-500">
            We found {meds.length} medicine{meds.length === 1 ? "" : "s"}. Please review before we
            create your reminders.
          </p>
        </div>
        <LanguageToggle />
      </div>

      {(prescription.diagnoses.length > 0 || prescription.symptoms.length > 0) && (
        <Card className="p-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            From the prescription
          </p>
          {prescription.diagnoses.length > 0 && (
            <p className="text-sm text-slate-700">
              <span className="font-medium">Diagnosis: </span>
              {translatedDiagnoses.join(", ")}
            </p>
          )}
          {prescription.symptoms.length > 0 && (
            <p className="text-sm text-slate-700">
              <span className="font-medium">Symptoms: </span>
              {translatedSymptoms.join(", ")}
            </p>
          )}
        </Card>
      )}

      <div className="flex flex-col gap-3">
        {meds.map((med, i) => {
          const flagged = needsReview(med);
          const editing = editingIndex === i;
          return (
            <Card key={i} className="p-4">
              <div className="mb-2 flex items-start justify-between">
                <div>
                  <p className="text-base font-semibold uppercase text-slate-900">
                    {translatedNames[i]}
                  </p>
                  {med.strength && <p className="text-sm text-slate-500">{med.strength}</p>}
                </div>
                {flagged && <ReviewBadge />}
              </div>

              {editing ? (
                <div className="flex flex-col gap-2">
                  <LabeledInput
                    label="Dose"
                    value={med.dose || ""}
                    onChange={(v) => updateMed(i, { dose: v })}
                  />
                  <LabeledInput
                    label="Frequency"
                    value={med.frequency || ""}
                    onChange={(v) => updateMed(i, { frequency: v })}
                    hint="e.g. 1-0-1, twice daily, morning"
                  />
                  <LabeledInput
                    label="Duration"
                    value={med.duration || ""}
                    onChange={(v) => updateMed(i, { duration: v })}
                  />
                  <LabeledInput
                    label="Food instruction"
                    value={med.food_instruction || ""}
                    onChange={(v) => updateMed(i, { food_instruction: v })}
                  />
                  <button
                    onClick={() => setEditingIndex(null)}
                    className="mt-1 rounded-full bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <div className="flex flex-col gap-1 text-sm text-slate-600">
                  {med.dose && <p>{translatedDoses[i]}</p>}
                  <p>{med.frequency || "No frequency extracted"}</p>
                  {med.duration && <p>{translatedDurations[i]}</p>}
                  {med.food_instruction && (
                    <p className="text-teal-700">Take {translatedFoodInstructions[i]?.toLowerCase()}</p>
                  )}
                  <button
                    onClick={() => setEditingIndex(i)}
                    className="mt-2 self-start text-sm font-medium text-teal-700 underline"
                  >
                    Edit
                  </button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      <button
        onClick={handleConfirm}
        disabled={submitting || meds.length === 0}
        className="rounded-full bg-teal-600 px-4 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-50"
      >
        {submitting ? "Confirming..." : "Confirm Prescription"}
      </button>
    </div>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  hint?: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:border-teal-400 focus:outline-none"
      />
      {hint && <span className="text-[11px] font-normal text-slate-400">{hint}</span>}
    </label>
  );
}
