"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/Card";
import { ErrorState } from "@/components/States";

const STEPS = ["Reading medicines", "Checking dosage", "Preparing your medication schedule"];

export default function UploadPrescriptionPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [stage, setStage] = useState<"idle" | "uploading" | "extracting">("idle");
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<ApiError | null>(null);

  const handleFile = (f: File | null) => {
    setError(null);
    setFile(f);
    if (f && f.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(f));
    } else {
      setPreview(null);
    }
  };

  const handleSubmit = async () => {
    if (!file) return;
    setError(null);
    setStage("uploading");
    try {
      const prescription = await api.uploadPrescription(file);
      setStage("extracting");

      const stepTimer = setInterval(() => {
        setStepIndex((i) => Math.min(i + 1, STEPS.length - 1));
      }, 1200);

      try {
        await api.extractPrescription(prescription.id);
      } finally {
        clearInterval(stepTimer);
      }

      router.push(`/prescriptions/${prescription.id}`);
    } catch (e) {
      setStage("idle");
      setError(
        e instanceof ApiError
          ? e
          : new ApiError("We couldn't process this prescription.", 0),
      );
    }
  };

  if (stage === "extracting") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 p-6 text-center">
        <div className="h-14 w-14 animate-spin rounded-full border-4 border-teal-100 border-t-teal-600" />
        <h1 className="text-lg font-semibold text-slate-800">Scanning prescription...</h1>
        <div className="flex flex-col gap-2 text-sm">
          {STEPS.map((step, i) => (
            <div
              key={step}
              className={`flex items-center gap-2 transition ${
                i <= stepIndex ? "text-teal-700" : "text-slate-300"
              }`}
            >
              <span>{i < stepIndex ? "✓" : i === stepIndex ? "…" : "○"}</span>
              {step}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="pt-2 text-xl font-semibold text-slate-900">Scan Prescription</h1>
      <p className="text-sm text-slate-500">
        Upload a clear photo or PDF of your prescription. Dawa Dost will read the medicines for
        you to confirm.
      </p>

      {error && (
        <ErrorState
          title="We couldn't read this prescription clearly."
          description={error.message}
          hint={error.hint || "Please upload a clearer photo or enter the medicine details manually."}
          onRetry={() => setError(null)}
        />
      )}

      <Card className="p-5">
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
        />

        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={preview}
            alt="Prescription preview"
            className="mx-auto mb-4 max-h-64 rounded-xl object-contain"
          />
        ) : file ? (
          <div className="mb-4 flex flex-col items-center gap-2 text-slate-500">
            <span className="text-4xl">📄</span>
            <p className="text-sm">{file.name}</p>
          </div>
        ) : (
          <div className="mb-4 flex flex-col items-center gap-2 py-8 text-slate-400">
            <span className="text-4xl">📷</span>
            <p className="text-sm">No file selected yet</p>
          </div>
        )}

        <button
          onClick={() => inputRef.current?.click()}
          className="w-full rounded-full bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200"
        >
          {file ? "Choose a different file" : "Choose photo or PDF"}
        </button>
      </Card>

      <button
        onClick={handleSubmit}
        disabled={!file || stage === "uploading"}
        className="rounded-full bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-50"
      >
        {stage === "uploading" ? "Uploading..." : "Submit for extraction"}
      </button>
    </div>
  );
}
