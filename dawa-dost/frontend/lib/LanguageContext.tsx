"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type LanguageCode = "en-IN" | "hi-IN";

export const LANGUAGE_LABELS: Record<LanguageCode, string> = {
  "en-IN": "EN",
  "hi-IN": "हिं",
};

interface LanguageContextValue {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
}

const LanguageContext = createContext<LanguageContextValue>({
  language: "en-IN",
  setLanguage: () => {},
});

const STORAGE_KEY = "dawa-dost-language";

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("en-IN");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "en-IN" || stored === "hi-IN") {
        setLanguageState(stored);
      }
    } catch {
      // localStorage unavailable - default to English
    }
  }, []);

  const setLanguage = (lang: LanguageCode) => {
    setLanguageState(lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // ignore
    }
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
