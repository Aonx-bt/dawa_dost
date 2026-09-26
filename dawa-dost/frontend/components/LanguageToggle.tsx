"use client";

import { LANGUAGE_LABELS, LanguageCode, useLanguage } from "@/lib/LanguageContext";

const OPTIONS: LanguageCode[] = ["en-IN", "hi-IN"];

export function LanguageToggle() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="inline-flex items-center gap-0.5 rounded-full bg-slate-100 p-0.5 text-xs font-semibold">
      {OPTIONS.map((code) => (
        <button
          key={code}
          onClick={() => setLanguage(code)}
          className={`rounded-full px-2.5 py-1 transition ${
            language === code ? "bg-white text-teal-700 shadow-sm" : "text-slate-500"
          }`}
        >
          {LANGUAGE_LABELS[code]}
        </button>
      ))}
    </div>
  );
}
